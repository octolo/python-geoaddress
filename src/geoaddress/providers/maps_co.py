from __future__ import annotations

import time
from typing import Any

from . import GeoaddressProvider


class MapsCoProvider(GeoaddressProvider):
    name = "maps_co"
    display_name = "Maps.co"
    description = "Maps.co provider"
    required_packages = ["requests"]
    documentation_url = "https://geocode.maps.co/docs/"
    site_url = "https://geocode.maps.co"
    config_keys = ["MAPS_CO_API_KEY", "MAPS_CO_BASE_URL"]
    config_defaults = {
        "MAPS_CO_BASE_URL": "https://geocode.maps.co",
    }
    config_required = ["MAPS_CO_API_KEY"]

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize Maps.co provider."""
        super().__init__(**kwargs)
        self._base_url = self._get_config_or_env("MAPS_CO_BASE_URL", "https://geocode.maps.co")
        self._api_key = self._get_config_or_env("MAPS_CO_API_KEY")
        self._last_request_time = 0.0

    _field_mapping: dict[str, Any] = {
        "reference": lambda r: str(r.get("place_id")) if r.get("place_id") else None,
        "address_line1": lambda r: (
            f"{r.get('address', {}).get('house_number', '')} {r.get('address', {}).get('road', '')}".strip()
            if r.get("address", {}).get("house_number") and r.get("address", {}).get("road")
            else r.get("address", {}).get("road", "")
        ),
        "address_line2": "",
        "address_line3": "",
        "city": lambda r: (
            r.get("address", {}).get("city")
            or r.get("address", {}).get("town")
            or r.get("address", {}).get("village")
            or ""
        ),
        "postal_code": "address.postcode",
        "state": lambda r: r.get("address", {}).get("state") or r.get("address", {}).get("province") or "",
        "region": "address.region",
        "country_code": lambda r: (r.get("address", {}).get("country_code", "") or "").upper(),
        "country": lambda r: r.get("address", {}).get("country", "") or "",
        "municipality": "address.municipality",
        "neighbourhood": lambda r: (
            r.get("address", {}).get("quarter")
            or r.get("address", {}).get("neighbourhood")
            or r.get("address", {}).get("suburb")
            or ""
        ),
        "address_type": lambda r: (
            (
                r.get("type")
                if r.get("class") in ("place", "highway")
                else (r.get("type") or "building")
                if r.get("class") == "building"
                else (f"{r.get('class')}_{r.get('type')}" if r.get("type") else r.get("class"))
            )
            if r.get("class") and r.get("type")
            else (r.get("class") or r.get("type") or "")
        ),
        "latitude": lambda r: float(r["lat"]) if r.get("lat") else None,
        "longitude": lambda r: float(r["lon"]) if r.get("lon") else None,
        "osm_id": lambda r: int(r["osm_id"]) if r.get("osm_id") is not None else None,
        "osm_type": lambda r: r.get("osm_type", "").upper() if r.get("osm_type") else None,
    }

    def search_addresses(self, query: str, raw: bool = False, proximity: str | None = None) -> list[dict[str, Any]]:  # noqa: C901

        """Search addresses using Maps.co."""
        if not self._api_key:
            if raw:
                return [{"error": "MAPS_CO_API_KEY not configured"}]
            return []

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "api_key": self._api_key,
            "q": query,
            "format": "json",
            "addressdetails": 1,
            "limit": 10,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["lat"] = str(lat)
            params["lon"] = str(lon)

        try:
            response = requests.get(f"{self._base_url}/search", params=params, timeout=10)
            response.raise_for_status()
            results = response.json()

            if raw:
                return results if isinstance(results, list) else [results] if results else []

            if isinstance(results, dict):
                if "error" in results:
                    return []
                results = [results]

            if not isinstance(results, list):
                return []

            addresses = []
            for feature in results:
                normalized = self._normalize_from_mapping(feature, self._field_mapping)
                normalized["backend"] = self.display_name
                normalized["backend_name"] = self.name
                normalized["text"] = self._build_address_string(normalized)
                normalized["confidence"] = self._calculate_confidence(
                    normalized,
                    feature=feature,
                    importance_key="importance",
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

        """Reverse geocode coordinates to an address using Maps.co."""
        if not self._api_key:
            if raw:
                return {"error": "MAPS_CO_API_KEY not configured"}
            return None

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "api_key": self._api_key,
            "lat": str(latitude),
            "lon": str(longitude),
            "format": "json",
            "addressdetails": 1,
        }

        try:
            response = requests.get(f"{self._base_url}/reverse", params=params, timeout=10)
            response.raise_for_status()
            result = response.json()

            if raw:
                return result if isinstance(result, dict) else None

            if isinstance(result, dict) and "error" in result:
                return None

            if not isinstance(result, dict):
                return None

            normalized = self._normalize_from_mapping(result, self._field_mapping)
            normalized["backend"] = self.display_name
            normalized["backend_name"] = self.name
            normalized["text"] = self._build_address_string(normalized)
            normalized["confidence"] = self._calculate_confidence(
                normalized,
                feature=result,
                importance_key="importance",
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

    def get_address_by_reference(self, _reference: str, raw: bool = False) -> dict[str, Any] | None:  # noqa: C901

        """Get address by reference using Maps.co."""
        error_msg = "Maps.co does not support get_address_by_reference"
        if raw:
            return {"error": error_msg}
        return None

    def get_address_by_osm(self, osm_keys_value: dict[str, Any], raw: bool = False) -> list[dict[str, Any]] | None:  # noqa: C901

        """Get address by OSM key-value pairs or OSM ID using Maps.co."""
        if not self._api_key:
            if raw:
                return [{"error": "MAPS_CO_API_KEY not configured"}]
            return []

        if not osm_keys_value or not isinstance(osm_keys_value, dict):
            if raw:
                return [{"error": "osm_keys_value must be a non-empty dictionary"}]
            return []

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)
        self._last_request_time = time.time()

        headers: dict[str, str] = {}

        if "osm_id" in osm_keys_value and "osm_type" in osm_keys_value:
            osm_id = osm_keys_value.get("osm_id")
            osm_type = osm_keys_value.get("osm_type")

            if not osm_id or not osm_type:
                if raw:
                    return [{"error": "osm_id and osm_type are required when using OSM ID lookup"}]
                return []

            try:
                osm_id_int = int(osm_id)
                osm_type_str = str(osm_type).upper()
            except (ValueError, TypeError):
                if raw:
                    return [{"error": "Invalid OSM ID format"}]
                return []

            params = {
                "api_key": self._api_key,
                "osm_ids": f"{osm_type_str}{osm_id_int}",
                "format": "json",
                "addressdetails": 1,
            }

            try:
                response = requests.get(f"{self._base_url}/lookup", params=params, headers=headers, timeout=10)
                response.raise_for_status()
                results = response.json()

                if not isinstance(results, list):
                    return []

                if raw:
                    return results

                addresses = []
                for feature in results:
                    normalized = self._normalize_from_mapping(feature, self._field_mapping)
                    normalized["backend"] = self.display_name
                    normalized["backend_name"] = self.name
                    normalized["text"] = self._build_address_string(normalized)
                    normalized["confidence"] = self._calculate_confidence(
                        normalized,
                        feature=feature,
                        importance_key="importance",
                    )
                    normalized["geoaddress_id"] = self._generate_geoaddress_id(normalized)
                    normalized = self._order_normalized_fields(normalized)
                    addresses.append(normalized)

                return addresses
            except Exception:
                return []
        else:
            query_parts = []
            for key, value in osm_keys_value.items():
                if key and value:
                    query_parts.append(f"[{key}={value}]")

            if not query_parts:
                if raw:
                    return [{"error": "At least one valid OSM key-value pair is required"}]
                return []

            query = "".join(query_parts)

            params = {
                "api_key": self._api_key,
                "q": query,
                "format": "json",
                "addressdetails": 1,
                "limit": 10,
            }

            try:
                response = requests.get(f"{self._base_url}/search", params=params, headers=headers, timeout=10)
                response.raise_for_status()
                results = response.json()

                if raw:
                    return results if isinstance(results, list) else [results] if results else []

                if isinstance(results, dict):
                    if "error" in results:
                        return []
                    results = [results]

                if not isinstance(results, list):
                    return []

                addresses = []
                for feature in results:
                    normalized = self._normalize_from_mapping(feature, self._field_mapping)
                    normalized["backend"] = self.display_name
                    normalized["backend_name"] = self.name
                    normalized["text"] = self._build_address_string(normalized)
                    normalized["confidence"] = self._calculate_confidence(
                        normalized,
                        feature=feature,
                        importance_key="importance",
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
