from __future__ import annotations

import time
from typing import Any

from . import GeoaddressProvider


class GeocodeEarthProvider(GeoaddressProvider):
    name = "geocode_earth"
    display_name = "Geocode Earth"
    description = "Geocode Earth provider"
    required_packages = ["requests"]
    documentation_url = "https://geocode.earth/docs"
    site_url = "https://geocode.earth"
    config_keys = ["GEOCODE_EARTH_API_KEY", "GEOCODE_EARTH_BASE_URL"]
    config_defaults = {
        "GEOCODE_EARTH_BASE_URL": "https://api.geocode.earth/v1",
    }
    config_required = ["GEOCODE_EARTH_API_KEY"]

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize Geocode Earth provider."""
        super().__init__(**kwargs)
        self._base_url = self._get_config_or_env("GEOCODE_EARTH_BASE_URL", "https://api.geocode.earth/v1")
        api_key = self._get_config_or_env("GEOCODE_EARTH_API_KEY")
        self._api_key = api_key.strip() if api_key else None
        self._last_request_time = 0.0

    def _extract_address_from_feature(self, feature: dict[str, Any]) -> dict[str, Any]:  # noqa: C901

        """Extract address components from a Geocode Earth/Pelias feature."""
        properties = feature.get("properties", {})
        geometry = feature.get("geometry", {})

        address_line1_parts = []
        if properties.get("housenumber"):
            address_line1_parts.append(properties["housenumber"])
        if properties.get("street"):
            address_line1_parts.append(properties["street"])
        address_line1 = " ".join(address_line1_parts).strip()

        if not address_line1:
            address_line1 = properties.get("name", "")

        geometry.get("coordinates", [])

        city = (
            properties.get("locality", "")
            or properties.get("localadmin", "")
            or properties.get("county", "")
            or ""
        )

        municipality = properties.get("municipality", "")
        state = properties.get("state", "")
        region = properties.get("region", "")

        neighbourhood = (
            properties.get("neighbourhood", "")
            or properties.get("suburb", "")
            or properties.get("district", "")
            or ""
        )

        address_type = properties.get("layer", "") or properties.get("type", "")

        reference = properties.get("gid") or feature.get("id")

        return {
            "address_line1": address_line1 or "",
            "address_line2": "",
            "address_line3": "",
            "city": city,
            "postal_code": properties.get("postalcode", ""),
            "state": state,
            "region": region,
            "country_code": (
                properties.get("country_a", "").upper() if properties.get("country_a") else ""
            ),
            "country": properties.get("country", "") or "",
            "municipality": municipality,
            "neighbourhood": neighbourhood,
            "address_type": address_type,
            "reference": str(reference) if reference is not None else None,
        }

    def search_addresses(self, query: str, raw: bool = False, proximity: str | None = None) -> list[dict[str, Any]]:  # noqa: C901

        """Search addresses using Geocode Earth."""
        if not self._api_key:
            if raw:
                return [{"error": "GEOCODE_EARTH_API_KEY not configured"}]
            return []

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.5:
            time.sleep(0.5 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "api_key": self._api_key,
            "text": query,
            "size": 10,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["focus.point.lat"] = str(lat)
            params["focus.point.lon"] = str(lon)

        try:
            response = requests.get(
                f"{self._base_url}/autocomplete",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()

            if raw:
                if isinstance(result, dict) and "features" in result:
                    features = result.get("features", [])
                    return list(features) if isinstance(features, list) else []
                return [result] if isinstance(result, dict) else []

            if isinstance(result, dict) and "error" in result:
                return []

            features = result.get("features", []) if isinstance(result, dict) else []
            if not isinstance(features, list) or len(features) == 0:
                return []
            features_list: list[dict[str, Any]] = list(features)

            addresses = []
            for feature in features_list:
                try:
                    normalized = self._extract_address_from_feature(feature)

                    coords = feature.get("geometry", {}).get("coordinates", [])
                    if len(coords) >= 2:
                        normalized["longitude"] = float(coords[0])
                        normalized["latitude"] = float(coords[1])

                    normalized["backend"] = self.display_name
                    normalized["backend_name"] = self.name
                    normalized["text"] = self._build_address_string(normalized)

                    normalized["confidence"] = self._calculate_confidence(
                        normalized,
                        feature=feature,
                        importance_key="properties.confidence",
                    )
                    normalized["relevance"] = self._calculate_relevance(
                        {"address_line1": query},
                        normalized,
                    )
                    normalized["geoaddress_id"] = self._generate_geoaddress_id(normalized)
                    normalized = self._order_normalized_fields(normalized)
                    addresses.append(normalized)
                except Exception:
                    continue

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

        """Reverse geocode coordinates to an address using Geocode Earth."""
        if not self._api_key:
            if raw:
                return {"error": "GEOCODE_EARTH_API_KEY not configured"}
            return None

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.5:
            time.sleep(0.5 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "api_key": self._api_key,
            "point.lat": latitude,
            "point.lon": longitude,
        }

        try:
            response = requests.get(
                f"{self._base_url}/reverse",
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

            normalized["backend"] = self.display_name
            normalized["backend_name"] = self.name
            normalized["text"] = self._build_address_string(normalized)

            normalized["confidence"] = self._calculate_confidence(
                normalized,
                feature=feature,
                importance_key="properties.confidence",
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

    def get_address_by_reference(self, reference: str, raw: bool = False) -> dict[str, Any] | None:  # noqa: C901

        """Get address by reference (GID) using Geocode Earth."""
        if not self._api_key:
            if raw:
                return {"error": "GEOCODE_EARTH_API_KEY not configured"}
            return None

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.5:
            time.sleep(0.5 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "api_key": self._api_key,
            "ids": reference,
        }

        try:
            response = requests.get(
                f"{self._base_url}/place",
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

            normalized["confidence"] = self._calculate_confidence(
                normalized,
                feature=feature,
                importance_key="properties.confidence",
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
