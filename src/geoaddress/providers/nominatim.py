from __future__ import annotations

import time
from typing import Any

from . import GeoaddressProvider


class NominatimProvider(GeoaddressProvider):
    name = "nominatim"
    display_name = "Nominatim"
    description = "Nominatim provider"
    required_packages = ["requests"]
    documentation_url = "https://nominatim.org/release-docs/develop/api/Overview/"
    site_url = "https://nominatim.org"
    config_keys = ["NOMINATIM_BASE_URL", "NOMINATIM_USER_AGENT"]
    config_defaults = {
        "NOMINATIM_BASE_URL": "https://nominatim.openstreetmap.org",
        "NOMINATIM_USER_AGENT": "python-geoaddress/1.0",
    }
    config_required = ["NOMINATIM_USER_AGENT"]

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize Nominatim provider."""
        super().__init__(**kwargs)
        self._base_url = self._get_config_or_env("NOMINATIM_BASE_URL", "https://nominatim.openstreetmap.org")
        self._user_agent = self._get_config_or_env("NOMINATIM_USER_AGENT", "python-geoaddress/1.0")
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

        """Search addresses using Nominatim."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "q": query,
            "format": "json",
            "addressdetails": 1,
            "limit": 10,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["lat"] = str(lat)
            params["lon"] = str(lon)

        headers = {"User-Agent": self._user_agent}

        try:
            response = requests.get(f"{self._base_url}/search", params=params, headers=headers, timeout=10)
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
        except Exception:
            return []

    def reverse_geocode(self, latitude: float, longitude: float, raw: bool = False) -> dict[str, Any] | None:  # noqa: C901

        """Reverse geocode coordinates to an address using Nominatim."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "lat": str(latitude),
            "lon": str(longitude),
            "format": "json",
            "addressdetails": 1,
        }
        headers = {"User-Agent": self._user_agent}

        try:
            response = requests.get(f"{self._base_url}/reverse", params=params, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()

            if not isinstance(result, dict):
                return None

            if raw:
                return result

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
        except Exception:
            return None

    def get_address_by_reference(self, reference: str, raw: bool = False) -> dict[str, Any] | None:  # noqa: C901

        """Get address by reference (place_id) using Nominatim."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "place_id": reference,
            "format": "json",
            "addressdetails": 1,
        }
        headers = {"User-Agent": self._user_agent}

        try:
            response = requests.get(f"{self._base_url}/details", params=params, headers=headers, timeout=10)
            response.raise_for_status()
            result = response.json()

            if not isinstance(result, dict):
                return None

            if raw:
                return result

            addresstags = result.get("addresstags", {})
            centroid = result.get("centroid", {})
            geometry = result.get("geometry", {})

            coordinates = centroid.get("coordinates") or geometry.get("coordinates")
            lat = coordinates[1] if coordinates and len(coordinates) >= 2 else None
            lon = coordinates[0] if coordinates and len(coordinates) >= 2 else None

            transformed_result = {
                "place_id": result.get("place_id"),
                "osm_id": result.get("osm_id"),
                "osm_type": result.get("osm_type"),
                "lat": str(lat) if lat is not None else None,
                "lon": str(lon) if lon is not None else None,
                "type": result.get("type"),
                "class": result.get("category"),
                "address": {
                    "house_number": addresstags.get("housenumber") or result.get("housenumber"),
                    "road": addresstags.get("street"),
                    "city": addresstags.get("city"),
                    "town": addresstags.get("town"),
                    "village": addresstags.get("village"),
                    "postcode": addresstags.get("postcode") or result.get("calculated_postcode"),
                    "state": addresstags.get("state"),
                    "province": addresstags.get("province"),
                    "country_code": result.get("country_code"),
                    "country": addresstags.get("country"),
                    "municipality": addresstags.get("municipality"),
                    "region": addresstags.get("region"),
                    "quarter": addresstags.get("quarter"),
                    "neighbourhood": addresstags.get("neighbourhood"),
                    "suburb": addresstags.get("suburb"),
                },
                "importance": result.get("calculated_importance") or result.get("importance"),
            }

            normalized = self._normalize_from_mapping(transformed_result, self._field_mapping)
            normalized["backend"] = self.display_name
            normalized["backend_name"] = self.name
            normalized["text"] = self._build_address_string(normalized)
            normalized["confidence"] = self._calculate_confidence(
                normalized,
                feature=transformed_result,
                importance_key="importance",
            )
            normalized["geoaddress_id"] = self._generate_geoaddress_id(normalized)
            normalized = self._order_normalized_fields(normalized)

            return normalized
        except requests.exceptions.Timeout:
            raise requests.exceptions.Timeout("Request timeout after 10 seconds")
        except Exception:
            return None

    def get_address_by_osm(self, osm_keys_value: dict[str, Any], raw: bool = False) -> list[dict[str, Any]] | None:  # noqa: C901

        """Get address by OSM key-value pairs or OSM ID using Nominatim.

        Args:
            osm_keys_value: Dictionary containing either:
                - OSM tags (e.g., {"place": "city", "name": "Paris"})
                - OSM ID (e.g., {"osm_id": 9550582112, "osm_type": "N"})
            raw: If True, return raw provider response.
        """
        if not osm_keys_value or not isinstance(osm_keys_value, dict):
            if raw:
                return [{"error": "osm_keys_value must be a non-empty dictionary"}]
            return []

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)
        self._last_request_time = time.time()

        headers = {"User-Agent": self._user_agent}

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
            except requests.exceptions.Timeout:
                raise requests.exceptions.Timeout("Request timeout after 10 seconds")
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
                "q": query,
                "format": "json",
                "addressdetails": 1,
                "limit": 10,
            }

            try:
                response = requests.get(f"{self._base_url}/search", params=params, headers=headers, timeout=10)
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
            except requests.exceptions.Timeout:
                raise requests.exceptions.Timeout("Request timeout after 10 seconds")
            except Exception:
                return []
