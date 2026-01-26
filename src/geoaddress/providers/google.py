from __future__ import annotations

from typing import Any

import requests

from .base import GeoaddressProvider

GOOGLE_ADDRESSES_AUTOCOMPLETE_SOURCE = {
    'city': ['address_components.locality', 'address_components.postal_town'],
    'postal_code': ['address_components.postal_code'],
    'county': ['address_components.administrative_area_level_2'],
    'state': ['address_components.administrative_area_level_1'],
    'region': ['address_components.administrative_area_level_2'],
    'country_code': ['address_components.country'],
    'country': ['address_components.country'],
    'municipality': ['address_components.administrative_area_level_3', 'address_components.sublocality_level_1'],
    'neighbourhood': ['address_components.neighborhood', 'address_components.sublocality'],
    'address_type': ['types'],
    'latitude': ['geometry.location.lat'],
    'longitude': ['geometry.location.lng'],
    'number': ['address_components.street_number'],
    'street': ['address_components.route'],
}


class GoogleMapsProvider(GeoaddressProvider):
    name = "google_maps"
    display_name = "Google Maps"
    description = "Google Maps provider"
    required_packages = ["requests"]
    documentation_url = "https://developers.google.com/maps/documentation/geocoding"
    site_url = "https://developers.google.com/maps"
    config_keys = ["API_KEY"]
    cost_addresses_autocomplete = 0.005
    cost_search_addresses = 0.005
    cost_reverse_geocode = 0.005
    fields_associations = GOOGLE_ADDRESSES_AUTOCOMPLETE_SOURCE

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize Google Maps provider."""
        super().__init__(**kwargs)
        self._base_url = "https://maps.googleapis.com/maps/api"
        self._api_key = self._get_config_or_env("API_KEY")


    def _extract_component_by_type(self, address_components: list[dict[str, Any]], types_list: list[str]) -> dict[str, str]:
        """Extract component by types from address_components."""
        for component in address_components:
            component_types = component.get("types", [])
            if any(t in component_types for t in types_list):
                return {
                    "long_name": component.get("long_name", ""),
                    "short_name": component.get("short_name", ""),
                }
        return {"long_name": "", "short_name": ""}

    def get_normalize_address_line1(self, data: dict[str, Any]) -> str:
        address_components = data.get("address_components", [])
        street_number = self._extract_component_by_type(address_components, ["street_number"])
        route = self._extract_component_by_type(address_components, ["route"])
        street_number_val = street_number.get("long_name", "")
        route_val = route.get("long_name", "")
        if street_number_val and route_val:
            return f"{street_number_val} {route_val}".strip()
        if route_val:
            return route_val
        return ""

    def get_normalize_city(self, data: dict[str, Any]) -> str:
        address_components = data.get("address_components", [])
        city_component = self._extract_component_by_type(address_components, ["locality", "postal_town"])
        return city_component.get("long_name", "") or ""

    def get_normalize_postal_code(self, data: dict[str, Any]) -> str:
        address_components = data.get("address_components", [])
        postal_component = self._extract_component_by_type(address_components, ["postal_code"])
        return postal_component.get("long_name", "") or ""

    def get_normalize_county(self, data: dict[str, Any]) -> str:
        address_components = data.get("address_components", [])
        county_component = self._extract_component_by_type(address_components, ["administrative_area_level_2"])
        return county_component.get("long_name", "") or ""

    def get_normalize_state(self, data: dict[str, Any]) -> str:
        address_components = data.get("address_components", [])
        state_component = self._extract_component_by_type(address_components, ["administrative_area_level_1"])
        return state_component.get("long_name", "") or ""

    def get_normalize_region(self, data: dict[str, Any]) -> str:
        address_components = data.get("address_components", [])
        region_component = self._extract_component_by_type(address_components, ["administrative_area_level_2"])
        return region_component.get("long_name", "") or ""

    def get_normalize_country_code(self, data: dict[str, Any]) -> str:
        address_components = data.get("address_components", [])
        country_component = self._extract_component_by_type(address_components, ["country"])
        country_code = country_component.get("short_name", "")
        return country_code.upper() if country_code else ""

    def get_normalize_country(self, data: dict[str, Any]) -> str:
        address_components = data.get("address_components", [])
        country_component = self._extract_component_by_type(address_components, ["country"])
        return country_component.get("long_name", "") or ""

    def get_normalize_municipality(self, data: dict[str, Any]) -> str:
        address_components = data.get("address_components", [])
        municipality_component = self._extract_component_by_type(address_components, ["administrative_area_level_3", "sublocality_level_1"])
        return municipality_component.get("long_name", "") or ""

    def get_normalize_neighbourhood(self, data: dict[str, Any]) -> str:
        address_components = data.get("address_components", [])
        neighbourhood_component = self._extract_component_by_type(address_components, ["neighborhood", "sublocality"])
        return neighbourhood_component.get("long_name", "") or ""

    def get_normalize_address_type(self, data: dict[str, Any]) -> str:
        types_list = data.get("types", [])
        if types_list and isinstance(types_list, list):
            return types_list[0] if types_list else ""
        return str(types_list) if types_list else ""

    def get_normalize_latitude(self, data: dict[str, Any]) -> float | None:
        geometry = data.get("geometry", {})
        location = geometry.get("location", {})
        lat_val = location.get("lat")
        return float(lat_val) if lat_val is not None else None

    def get_normalize_longitude(self, data: dict[str, Any]) -> float | None:
        geometry = data.get("geometry", {})
        location = geometry.get("location", {})
        lng_val = location.get("lng")
        return float(lng_val) if lng_val is not None else None

    def search_addresses(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Search addresses using Google Maps."""
        self.addresses_autocomplete_query = query
        kwargs.pop('raw', False)
        proximity = kwargs.pop('proximity', None)
        if not self._api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY not configured")

        params = {
            "key": self._api_key,
            "address": query,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["location"] = f"{lat},{lon}"

        response = requests.get(
            f"{self._base_url}/geocode/json",
            params=params,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        if result.get("status") != "OK":
            return []
        results_list = result.get("results", []) if isinstance(result, dict) else []
        return results_list if isinstance(results_list, list) else []

    def addresses_autocomplete(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Search addresses using Google Maps."""
        self.addresses_autocomplete_query = query
        proximity = kwargs.pop('proximity', None)
        if not self._api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY not configured")

        params = {
            "key": self._api_key,
            "address": query,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["location"] = f"{lat},{lon}"

        response = requests.get(
            f"{self._base_url}/geocode/json",
            params=params,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        if result.get("status") != "OK":
            return []
        results_list = result.get("results", []) if isinstance(result, dict) else []
        return results_list if isinstance(results_list, list) else []

    def reverse_geocode(self, latitude: float | None = None, longitude: float | None = None, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Reverse geocode coordinates to an address using Google Maps."""
        if latitude is None:
            latitude = kwargs.pop('latitude', None)
        if longitude is None:
            longitude = kwargs.pop('longitude', None)
        if latitude is None or longitude is None:
            raise ValueError("latitude and longitude are required")

        if not self._api_key:
            raise ValueError("GOOGLE_MAPS_API_KEY not configured")

        self.reverse_geocode_latitude = latitude
        self.reverse_geocode_longitude = longitude

        params = {
            "key": self._api_key,
            "latlng": f"{latitude},{longitude}",
        }

        response = requests.get(
            f"{self._base_url}/geocode/json",
            params=params,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        if result.get("status") != "OK":
            return []
        results_list = result.get("results", []) if isinstance(result, dict) else []
        return results_list if isinstance(results_list, list) else []

