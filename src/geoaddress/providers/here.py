from __future__ import annotations

import time
from typing import Any

from . import GeoaddressProvider


class HereProvider(GeoaddressProvider):
    name = "here"
    display_name = "Here"
    description = "Here provider"
    required_packages = ["requests"]
    documentation_url = "https://developer.here.com/documentation/geocoding-search-api"
    site_url = "https://developer.here.com"
    config_keys = ["HERE_APP_ID", "HERE_APP_CODE"]
    config_required = ["HERE_APP_ID", "HERE_APP_CODE"]

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize Here provider."""
        super().__init__(**kwargs)
        self._base_url = "https://geocoder.api.here.com/6.2"
        self._app_id = self._get_config_or_env("HERE_APP_ID")
        self._app_code = self._get_config_or_env("HERE_APP_CODE")
        self._last_request_time = 0.0

    def _extract_address_from_result(self, result: dict[str, Any]) -> dict[str, Any]:  # noqa: C901

        """Extract address components from a Here result."""
        location = result.get("Location", {})
        address = location.get("Address", {})

        address_line1 = ""
        street = address.get("Street", "")
        house_number = address.get("HouseNumber", "")
        if house_number and street:
            address_line1 = f"{house_number} {street}".strip()
        elif street:
            address_line1 = street

        city = address.get("City", "")
        postal_code = address.get("PostalCode", "")
        state = address.get("State", "")
        region = address.get("County", "") or address.get("Region", "")
        country_code = address.get("Country", "").upper()
        country = address.get("Country", "")

        municipality = address.get("Municipality", "") or address.get("District", "")
        neighbourhood = address.get("Subdistrict", "") or address.get("Neighborhood", "")

        location_id = location.get("LocationId")

        return {
            "address_line1": address_line1,
            "address_line2": "",
            "address_line3": "",
            "city": city,
            "postal_code": postal_code,
            "state": state,
            "region": region,
            "country_code": country_code,
            "country": country,
            "municipality": municipality,
            "neighbourhood": neighbourhood,
            "address_type": "",
            "reference": str(location_id) if location_id else None,
        }

    def search_addresses(self, query: str, raw: bool = False, proximity: str | None = None) -> list[dict[str, Any]]:  # noqa: C901

        """Search addresses using Here."""
        if not self._app_id or not self._app_code:
            if raw:
                return [{"error": "HERE_APP_ID and HERE_APP_CODE must be configured"}]
            return []

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.1:
            time.sleep(0.1 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "app_id": self._app_id,
            "app_code": self._app_code,
            "searchtext": query,
            "maxresults": 10,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["prox"] = f"{lat},{lon},5000"

        try:
            response = requests.get(
                f"{self._base_url}/geocode.json",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()

            if raw:
                response_data = result.get("Response", {}) if isinstance(result, dict) else {}
                view = response_data.get("View", [])
                results_list = view[0].get("Result", []) if view else []
                return results_list if isinstance(results_list, list) else []

            if isinstance(result, dict) and "error" in result:
                return []

            response_data = result.get("Response", {}) if isinstance(result, dict) else {}
            view = response_data.get("View", [])
            if not view:
                return []

            results_list = view[0].get("Result", [])
            if not isinstance(results_list, list):
                return []

            addresses = []
            for item in results_list:
                try:
                    normalized = self._extract_address_from_result(item)

                    display_position = item.get("Location", {}).get("DisplayPosition", {})
                    if display_position:
                        lat_val = display_position.get("Latitude")
                        lon_val = display_position.get("Longitude")
                        if lat_val is not None:
                            normalized["latitude"] = float(lat_val)
                        if lon_val is not None:
                            normalized["longitude"] = float(lon_val)

                    normalized["backend"] = self.display_name
                    normalized["backend_name"] = self.name
                    normalized["text"] = self._build_address_string(normalized)

                    match_quality = item.get("MatchQuality", {})
                    relevance = match_quality.get("Relevance", 0.0) or 0.0
                    normalized["confidence"] = float(relevance)
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

        """Reverse geocode coordinates to an address using Here."""
        if not self._app_id or not self._app_code:
            if raw:
                return {"error": "HERE_APP_ID and HERE_APP_CODE must be configured"}
            return None

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.1:
            time.sleep(0.1 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "app_id": self._app_id,
            "app_code": self._app_code,
            "prox": f"{latitude},{longitude},250",
            "mode": "retrieveAddresses",
            "maxresults": 1,
        }

        try:
            response = requests.get(
                f"{self._base_url}/geocode.json",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()

            if raw:
                response_data = result.get("Response", {}) if isinstance(result, dict) else {}
                view = response_data.get("View", [])
                results_list = view[0].get("Result", []) if view else []
                return results_list[0] if results_list else None

            if isinstance(result, dict) and "error" in result:
                return None

            response_data = result.get("Response", {}) if isinstance(result, dict) else {}
            view = response_data.get("View", [])
            if not view:
                return None

            results_list = view[0].get("Result", [])
            if not results_list:
                return None

            item = results_list[0]
            normalized = self._extract_address_from_result(item)

            normalized["latitude"] = latitude
            normalized["longitude"] = longitude

            normalized["backend"] = self.display_name
            normalized["backend_name"] = self.name
            normalized["text"] = self._build_address_string(normalized)

            match_quality = item.get("MatchQuality", {})
            relevance = match_quality.get("Relevance", 0.0) or 0.0
            normalized["confidence"] = float(relevance)
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

        """Get address by reference (LocationId) using Here."""
        if not self._app_id or not self._app_code:
            if raw:
                return {"error": "HERE_APP_ID and HERE_APP_CODE must be configured"}
            return None

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.1:
            time.sleep(0.1 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "app_id": self._app_id,
            "app_code": self._app_code,
            "locationid": reference,
        }

        try:
            response = requests.get(
                f"{self._base_url}/geocode.json",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()

            if raw:
                response_data = result.get("Response", {}) if isinstance(result, dict) else {}
                view = response_data.get("View", [])
                results_list = view[0].get("Result", []) if view else []
                return results_list[0] if results_list else None

            if isinstance(result, dict) and "error" in result:
                return None

            response_data = result.get("Response", {}) if isinstance(result, dict) else {}
            view = response_data.get("View", [])
            if not view:
                return None

            results_list = view[0].get("Result", [])
            if not results_list:
                return None

            item = results_list[0]
            normalized = self._extract_address_from_result(item)

            display_position = item.get("Location", {}).get("DisplayPosition", {})
            if display_position:
                lat_val = display_position.get("Latitude")
                lon_val = display_position.get("Longitude")
                if lat_val is not None:
                    normalized["latitude"] = float(lat_val)
                if lon_val is not None:
                    normalized["longitude"] = float(lon_val)

            normalized["backend"] = self.display_name
            normalized["backend_name"] = self.name
            normalized["text"] = self._build_address_string(normalized)

            match_quality = item.get("MatchQuality", {})
            relevance = match_quality.get("Relevance", 0.0) or 0.0
            normalized["confidence"] = float(relevance)
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
