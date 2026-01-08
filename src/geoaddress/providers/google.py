from __future__ import annotations

import time
from typing import Any

from . import GeoaddressProvider


class GoogleMapsProvider(GeoaddressProvider):
    name = "google_maps"
    display_name = "Google Maps"
    description = "Google Maps provider"
    required_packages = ["requests"]
    documentation_url = "https://developers.google.com/maps/documentation/geocoding"
    site_url = "https://developers.google.com/maps"
    config_keys = ["API_KEY"]
    config_required = ["API_KEY"]
    cost_search_addresses = 0.005
    cost_reverse_geocode = 0.005
    cost_get_address_by_reference = 0.005

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize Google Maps provider."""
        super().__init__(**kwargs)
        self._base_url = "https://maps.googleapis.com/maps/api"
        self._api_key = self._get_config_or_env("API_KEY")
        self._last_request_time = 0.0

    def _extract_address_from_result(self, result: dict[str, Any]) -> dict[str, Any]:  # noqa: C901

        """Extract address components from a Google Maps result."""
        address_components = result.get("address_components", [])

        address_line1 = ""
        address_line2 = ""
        city = ""
        postal_code = ""
        state = ""
        region = ""
        county = ""
        municipality = ""
        neighbourhood = ""
        country_code = ""
        country = ""
        address_type = ""

        street_number = ""
        route = ""

        for component in address_components:
            types = component.get("types", [])
            long_name = component.get("long_name", "")
            short_name = component.get("short_name", "")

            if "street_number" in types:
                street_number = long_name
            elif "route" in types:
                route = long_name
            elif "locality" in types or "postal_town" in types:
                city = city if city else long_name
            elif "postal_code" in types:
                postal_code = long_name
            elif "administrative_area_level_1" in types:
                state = long_name
            elif "administrative_area_level_2" in types:
                county = long_name
                region = long_name
            elif "administrative_area_level_3" in types or "sublocality_level_1" in types:
                municipality = municipality if municipality else long_name
            elif "neighborhood" in types or "sublocality" in types:
                neighbourhood = neighbourhood if neighbourhood else long_name
            elif "country" in types:
                country_code = short_name.upper()
                country = long_name

        if street_number and route:
            address_line1 = f"{street_number} {route}".strip()
        elif route:
            address_line1 = route

        types_list = result.get("types", [])
        if types_list:
            address_type = types_list[0] if isinstance(types_list, list) else str(types_list)

        place_id = result.get("place_id")

        return {
            "address_line1": address_line1,
            "address_line2": address_line2,
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
            "reference": str(place_id) if place_id else None,
        }

    def search_addresses(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901
        """Search addresses using Google Maps."""
        raw = kwargs.pop('raw', False)
        proximity = kwargs.pop('proximity', None)
        if not self._api_key:
            if raw:
                return [{"error": "GOOGLE_MAPS_API_KEY not configured"}]
            return []

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.1:
            time.sleep(0.1 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "key": self._api_key,
            "address": query,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["location"] = f"{lat},{lon}"

        try:
            response = requests.get(
                f"{self._base_url}/geocode/json",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()

            if raw:
                results_list = result.get("results", []) if isinstance(result, dict) else []
                return results_list if isinstance(results_list, list) else []

            if isinstance(result, dict) and "error" in result:
                return []

            if result.get("status") != "OK":
                return []

            results_list = result.get("results", [])
            if not isinstance(results_list, list):
                return []

            addresses = []
            for item in results_list:
                try:
                    normalized = self._extract_address_from_result(item)

                    geometry = item.get("geometry", {})
                    location = geometry.get("location", {})
                    if location:
                        lat_val = location.get("lat")
                        lon_val = location.get("lng")
                        if lat_val is not None:
                            normalized["latitude"] = float(lat_val)
                        if lon_val is not None:
                            normalized["longitude"] = float(lon_val)

                    normalized["backend"] = self.display_name
                    normalized["backend_name"] = self.name
                    normalized["text"] = self._build_address_string(normalized)

                    location_type = geometry.get("location_type", "")
                    confidence_map = {
                        "ROOFTOP": 100.0,
                        "RANGE_INTERPOLATED": 90.0,
                        "GEOMETRIC_CENTER": 70.0,
                        "APPROXIMATE": 50.0,
                    }
                    normalized["confidence"] = confidence_map.get(location_type, 50.0)
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

        """Reverse geocode coordinates to an address using Google Maps."""
        if not self._api_key:
            if raw:
                return {"error": "GOOGLE_MAPS_API_KEY not configured"}
            return None

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.1:
            time.sleep(0.1 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "key": self._api_key,
            "latlng": f"{latitude},{longitude}",
        }

        try:
            response = requests.get(
                f"{self._base_url}/geocode/json",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()

            if raw:
                results_list = result.get("results", []) if isinstance(result, dict) else []
                return results_list[0] if results_list else None

            if isinstance(result, dict) and "error" in result:
                return None

            if result.get("status") != "OK":
                return None

            results_list = result.get("results", [])
            if not results_list:
                return None

            item = results_list[0]
            normalized = self._extract_address_from_result(item)

            normalized["latitude"] = latitude
            normalized["longitude"] = longitude

            normalized["backend"] = self.display_name
            normalized["backend_name"] = self.name
            normalized["text"] = self._build_address_string(normalized)

            geometry = item.get("geometry", {})
            location_type = geometry.get("location_type", "")
            confidence_map = {
                "ROOFTOP": 100.0,
                "RANGE_INTERPOLATED": 90.0,
                "GEOMETRIC_CENTER": 70.0,
                "APPROXIMATE": 50.0,
            }
            normalized["confidence"] = confidence_map.get(location_type, 50.0)
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

        """Get address by reference (place_id) using Google Maps."""
        if not self._api_key:
            if raw:
                return {"error": "GOOGLE_MAPS_API_KEY not configured"}
            return None

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.1:
            time.sleep(0.1 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "key": self._api_key,
            "place_id": reference,
        }

        try:
            response = requests.get(
                f"{self._base_url}/geocode/json",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()

            if raw:
                results_list = result.get("results", []) if isinstance(result, dict) else []
                return results_list[0] if results_list else None

            if isinstance(result, dict) and "error" in result:
                return None

            if result.get("status") != "OK":
                return None

            results_list = result.get("results", [])
            if not results_list:
                return None

            item = results_list[0]
            normalized = self._extract_address_from_result(item)

            geometry = item.get("geometry", {})
            location = geometry.get("location", {})
            if location:
                lat_val = location.get("lat")
                lon_val = location.get("lng")
                if lat_val is not None:
                    normalized["latitude"] = float(lat_val)
                if lon_val is not None:
                    normalized["longitude"] = float(lon_val)

            normalized["backend"] = self.display_name
            normalized["backend_name"] = self.name
            normalized["text"] = self._build_address_string(normalized)

            location_type = geometry.get("location_type", "")
            confidence_map = {
                "ROOFTOP": 100.0,
                "RANGE_INTERPOLATED": 90.0,
                "GEOMETRIC_CENTER": 70.0,
                "APPROXIMATE": 50.0,
            }
            normalized["confidence"] = confidence_map.get(location_type, 50.0)
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
