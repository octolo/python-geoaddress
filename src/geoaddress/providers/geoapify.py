from __future__ import annotations

import time
from typing import Any

from . import GeoaddressProvider


class GeoapifyProvider(GeoaddressProvider):
    name = "geoapify"
    display_name = "Geoapify"
    description = "Geoapify provider"
    required_packages = ["requests"]
    documentation_url = "https://apidocs.geoapify.com/docs/geocoding/"
    site_url = "https://www.geoapify.com"
    config_keys = ["GEOAPIFY_API_KEY", "GEOAPIFY_BASE_URL"]
    config_defaults = {
        "GEOAPIFY_BASE_URL": "https://api.geoapify.com/v1",
    }
    config_required = ["GEOAPIFY_API_KEY"]

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize Geoapify provider."""
        super().__init__(**kwargs)
        self._base_url = self._get_config_or_env("GEOAPIFY_BASE_URL", "https://api.geoapify.com/v1")
        self._api_key = self._get_config_or_env("GEOAPIFY_API_KEY")
        self._last_request_time = 0.0

    def _extract_address_from_feature(self, feature: dict[str, Any]) -> dict[str, Any]:  # noqa: C901
        """Extract address components from a Geoapify feature."""
        properties = feature.get("properties", {})

        address_line1 = properties.get("address_line1", "")
        if not address_line1:
            address_line1_parts = []
            if properties.get("housenumber"):
                address_line1_parts.append(str(properties["housenumber"]))
            if properties.get("street"):
                address_line1_parts.append(properties["street"])
            address_line1 = " ".join(address_line1_parts).strip()

        latitude = None
        longitude = None
        if "lat" in properties and properties["lat"] is not None:
            latitude = float(properties["lat"])
        if "lon" in properties and properties["lon"] is not None:
            longitude = float(properties["lon"])

        if latitude is None or longitude is None:
            geometry = feature.get("geometry", {})
            coordinates = geometry.get("coordinates", [])
            if len(coordinates) >= 2:
                if longitude is None:
                    longitude = float(coordinates[0])
                if latitude is None:
                    latitude = float(coordinates[1])

        city = (
            properties.get("city", "")
            or properties.get("town", "")
            or properties.get("village", "")
            or ""
        )

        municipality = properties.get("municipality", "")
        state = properties.get("state", "") or properties.get("state_code", "")
        region = properties.get("region", "")

        neighbourhood = (
            properties.get("neighbourhood", "")
            or properties.get("suburb", "")
            or properties.get("district", "")
            or properties.get("quarter", "")
            or ""
        )

        address_type = properties.get("type", "") or properties.get("category", "")

        reference = None
        if latitude is not None and longitude is not None:
            reference = f"{latitude}-{longitude}"

        return {
            "address_line1": address_line1 or "",
            "address_line2": "",
            "address_line3": "",
            "city": city,
            "postal_code": properties.get("postcode", ""),
            "state": state,
            "region": region,
            "country_code": (
                properties.get("country_code", "").upper() if properties.get("country_code") else ""
            ),
            "country": properties.get("country", "") or "",
            "municipality": municipality,
            "neighbourhood": neighbourhood,
            "address_type": address_type,
            "reference": str(reference) if reference is not None else None,
        }

    def search_addresses(self, query: str, raw: bool = False, proximity: str | None = None) -> list[dict[str, Any]]:  # noqa: C901

        """Search addresses using Geoapify."""
        if not self._api_key:
            if raw:
                return [{"error": "GEOAPIFY_API_KEY not configured"}]
            return []

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.1:
            time.sleep(0.1 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "apiKey": self._api_key,
            "text": query,
            "limit": 10,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["bias"] = f"proximity:{lon},{lat}"

        try:
            response = requests.get(
                f"{self._base_url}/geocode/search",
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

                properties = feature.get("properties", {})
                lat_prop = properties.get("lat")
                lon_prop = properties.get("lon")
                if lat_prop is not None:
                    normalized["latitude"] = float(lat_prop)
                if lon_prop is not None:
                    normalized["longitude"] = float(lon_prop)

                if normalized.get("latitude") is None or normalized.get("longitude") is None:
                    coords = feature.get("geometry", {}).get("coordinates", [])
                    if len(coords) >= 2:
                        normalized["longitude"] = float(coords[0])
                        normalized["latitude"] = float(coords[1])

                if normalized.get("latitude") is not None and normalized.get("longitude") is not None:
                    normalized["reference"] = f"{normalized['latitude']}-{normalized['longitude']}"

                normalized["backend"] = self.display_name
                normalized["backend_name"] = self.name
                normalized["text"] = self._build_address_string(normalized)

                normalized["confidence"] = self._calculate_confidence(
                    normalized,
                    feature=feature,
                    importance_key="properties.rank.confidence",
                )
                normalized["relevance"] = self._calculate_relevance(
                    {"address_line1": query},
                    normalized,
                )
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

        """Reverse geocode coordinates to an address using Geoapify."""
        if not self._api_key:
            if raw:
                return {"error": "GEOAPIFY_API_KEY not configured"}
            return None

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.1:
            time.sleep(0.1 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "apiKey": self._api_key,
            "lat": latitude,
            "lon": longitude,
        }

        try:
            response = requests.get(
                f"{self._base_url}/geocode/reverse",
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

            normalized["latitude"] = latitude
            normalized["longitude"] = longitude
            normalized["reference"] = f"{latitude}-{longitude}"

            normalized["backend"] = self.display_name
            normalized["backend_name"] = self.name
            normalized["text"] = self._build_address_string(normalized)

            normalized["confidence"] = self._calculate_confidence(
                normalized,
                feature=feature,
                importance_key="properties.rank.confidence",
            )
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

