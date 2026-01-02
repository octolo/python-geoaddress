from __future__ import annotations

import time
import urllib.parse
from typing import Any

from . import GeoaddressProvider


class MapboxProvider(GeoaddressProvider):
    name = "mapbox"
    display_name = "Mapbox"
    description = "Mapbox provider"
    required_packages = ["requests"]
    documentation_url = "https://docs.mapbox.com/api/search/geocoding/"
    site_url = "https://www.mapbox.com"
    config_keys = ["MAPBOX_ACCESS_TOKEN"]
    config_required = ["MAPBOX_ACCESS_TOKEN"]
    cost_search_addresses = 0.0005
    cost_reverse_geocode = 0.0005
    cost_get_address_by_reference = 0.0005

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize Mapbox provider."""
        super().__init__(**kwargs)
        self._base_url = "https://api.mapbox.com"
        self._access_token = self._get_config_or_env("MAPBOX_ACCESS_TOKEN")
        self._last_request_time = 0.0

    def _extract_context_value(self, context: list[dict[str, Any]], prefix: str) -> str:
        """Extract value from context array by id prefix."""
        for item in context:
            item_id = item.get("id", "")
            if item_id.startswith(prefix):
                return item.get("text", "")  # type: ignore[no-any-return]
        return ""

    def _extract_address_from_feature(self, feature: dict[str, Any]) -> dict[str, Any]:  # noqa: C901

        """Extract address components from a Mapbox feature."""
        properties = feature.get("properties", {})
        context = feature.get("context", [])

        address_line1 = properties.get("address", "")
        if not address_line1:
            place_name = feature.get("place_name", "")
            if place_name:
                parts = place_name.split(",")
                if parts:
                    address_line1 = parts[0].strip()

        if not address_line1:
            address_number = properties.get("address_number", "")
            street = properties.get("street", "")
            if address_number and street:
                address_line1 = f"{address_number} {street}".strip()
            elif street:
                address_line1 = street

        if not address_line1:
            text = feature.get("text", "")
            address_line1 = text if text else ""

        city = self._extract_context_value(context, "place")
        postal_code = self._extract_context_value(context, "postcode")
        county = self._extract_context_value(context, "county")
        state = ""
        region = ""
        for item in context:
            item_id = item.get("id", "")
            if item_id.startswith("region"):
                region_text = item.get("text", "")
                if region_text:
                    if not state:
                        state = region_text
                    else:
                        region = region_text

        municipality = self._extract_context_value(context, "district")
        neighbourhood = self._extract_context_value(context, "neighborhood")

        country_code = ""
        country = ""
        for item in context:
            item_id = item.get("id", "")
            if item_id.startswith("country"):
                country_code = item.get("short_code", "").upper()
                country = item.get("text", "")
                break

        address_type = properties.get("type", "")

        coords = feature.get("geometry", {}).get("coordinates", [])
        reference = None
        if len(coords) >= 2:
            latitude = float(coords[1])
            longitude = float(coords[0])
            reference = f"{latitude}-{longitude}"

        return {
            "address_line1": address_line1,
            "address_line2": "",
            "address_line3": "",
            "city": city,
            "postal_code": postal_code,
            "county": county,
            "state": state,
            "region": region,
            "country_code": country_code,
            "country": country,
            "municipality": municipality,
            "neighbourhood": neighbourhood,
            "address_type": address_type,
            "reference": reference,
        }

    def search_addresses(self, query: str, raw: bool = False, proximity: str | None = None) -> list[dict[str, Any]]:  # noqa: C901

        """Search addresses using Mapbox."""
        if not self._access_token:
            if raw:
                return [{"error": "MAPBOX_ACCESS_TOKEN not configured"}]
            return []

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.1:
            time.sleep(0.1 - time_since_last)
        self._last_request_time = time.time()

        encoded_query = urllib.parse.quote(query)
        params = {
            "access_token": self._access_token,
            "limit": 10,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["proximity"] = f"{lon},{lat}"

        try:
            response = requests.get(
                f"{self._base_url}/geocoding/v5/mapbox.places/{encoded_query}.json",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()

            if raw:
                features = result.get("features", []) if isinstance(result, dict) else []
                return features if isinstance(features, list) else []

            if isinstance(result, dict) and "error" in result:
                return []

            features = result.get("features", []) if isinstance(result, dict) else []
            if not isinstance(features, list):
                return []

            addresses = []
            for feature in features:
                normalized = self._extract_address_from_feature(feature)

                coords = feature.get("geometry", {}).get("coordinates", [])
                if len(coords) >= 2:
                    normalized["longitude"] = float(coords[0])
                    normalized["latitude"] = float(coords[1])

                normalized["backend"] = self.display_name
                normalized["backend_name"] = self.name
                normalized["text"] = self._build_address_string(normalized)
                normalized["confidence"] = self._calculate_confidence_heuristic(normalized)
                relevance_value = feature.get("relevance")
                if relevance_value is not None:
                    normalized["relevance"] = self._round_score(float(relevance_value) * 100.0)
                else:
                    normalized["relevance"] = 0.0
                normalized["geoaddress_id"] = self._generate_geoaddress_id(normalized)
                normalized = self._order_normalized_fields(normalized)
                addresses.append(normalized)

            return addresses
        except requests.exceptions.Timeout:
            raise requests.exceptions.Timeout("Request timeout after 10 seconds")
        except requests.exceptions.RequestException as e:
            if raw:
                return [{"error": str(e)}]
            return []
        except Exception as e:
            if raw:
                return [{"error": str(e)}]
            return []

    def reverse_geocode(self, latitude: float, longitude: float, raw: bool = False) -> dict[str, Any] | None:  # noqa: C901

        """Reverse geocode coordinates to an address using Mapbox."""
        if not self._access_token:
            if raw:
                return {"error": "MAPBOX_ACCESS_TOKEN not configured"}
            return None

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.1:
            time.sleep(0.1 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "access_token": self._access_token,
            "limit": 1,
        }

        try:
            response = requests.get(
                f"{self._base_url}/geocoding/v5/mapbox.places/{longitude},{latitude}.json",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()

            if raw:
                features = result.get("features", []) if isinstance(result, dict) else []
                return features[0] if features else None

            if isinstance(result, dict) and "error" in result:
                return None

            features = result.get("features", []) if isinstance(result, dict) else []
            if not features:
                return None

            feature = features[0]
            normalized = self._extract_address_from_feature(feature)

            coords = feature.get("geometry", {}).get("coordinates", [])
            if len(coords) >= 2:
                normalized["longitude"] = float(coords[0])
                normalized["latitude"] = float(coords[1])

            normalized["backend"] = self.display_name
            normalized["backend_name"] = self.name
            normalized["text"] = self._build_address_string(normalized)
            normalized["confidence"] = self._calculate_confidence_heuristic(normalized)
            relevance_value = feature.get("relevance")
            if relevance_value is not None:
                normalized["relevance"] = self._round_score(float(relevance_value) * 100.0)
            else:
                normalized["relevance"] = 0.0
            normalized["geoaddress_id"] = self._generate_geoaddress_id(normalized)
            normalized = self._order_normalized_fields(normalized)

            return normalized
        except requests.exceptions.Timeout:
            raise requests.exceptions.Timeout("Request timeout after 10 seconds")
        except requests.exceptions.RequestException as e:
            if raw:
                return {"error": str(e)}
            return None
        except Exception as e:
            if raw:
                return {"error": str(e)}
            return None

    def get_address_by_reference(self, reference: str, raw: bool = False) -> dict[str, Any] | None:
        """Get address by reference (latitude-longitude) using reverse geocoding."""
        return self.get_address_by_reference_latlon(reference, raw=raw)
