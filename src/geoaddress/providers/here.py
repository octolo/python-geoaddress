from __future__ import annotations

from typing import Any

import requests

from .base import GeoaddressProvider

HERE_ADDRESSES_AUTOCOMPLETE_SOURCE = {
    'city': ['Location.Address.City'],
    'postal_code': ['Location.Address.PostalCode'],
    'county': ['Location.Address.County'],
    'state': ['Location.Address.State'],
    'region': ['Location.Address.Region', 'Location.Address.County'],
    'country_code': ['Location.Address.Country'],
    'country': ['Location.Address.Country'],
    'municipality': ['Location.Address.Municipality', 'Location.Address.District'],
    'neighbourhood': ['Location.Address.Subdistrict', 'Location.Address.Neighborhood'],
    'address_type': [],
    'latitude': ['Location.DisplayPosition.Latitude'],
    'longitude': ['Location.DisplayPosition.Longitude'],
    'number': ['Location.Address.HouseNumber'],
    'street': ['Location.Address.Street'],
}


class HereProvider(GeoaddressProvider):
    name = "here"
    display_name = "Here"
    description = "Here provider"
    required_packages = ["requests"]
    documentation_url = "https://developer.here.com/documentation/geocoding-search-api"
    site_url = "https://developer.here.com"
    config_keys = ["APP_ID", "APP_CODE"]
    cost_addresses_autocomplete = 0.001
    cost_search_addresses = 0.001
    cost_reverse_geocode = 0.001
    fields_associations = HERE_ADDRESSES_AUTOCOMPLETE_SOURCE

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize Here provider."""
        super().__init__(**kwargs)
        self._base_url = "https://geocoder.api.here.com/6.2"
        self._app_id = self._get_config_or_env("APP_ID")
        self._app_code = self._get_config_or_env("APP_CODE")

    def get_normalize_address_line1(self, data: dict[str, Any]) -> str:
        location = data.get("Location", {})
        address = location.get("Address", {})
        street = address.get("Street", "")
        house_number = address.get("HouseNumber", "")
        if house_number and street:
            return f"{house_number} {street}".strip()
        if street:
            return street
        return ""

    def get_normalize_region(self, data: dict[str, Any]) -> str:
        location = data.get("Location", {})
        address = location.get("Address", {})
        region = address.get("Region", "")
        if not region:
            region = address.get("County", "")
        return region or ""

    def get_normalize_municipality(self, data: dict[str, Any]) -> str:
        location = data.get("Location", {})
        address = location.get("Address", {})
        return address.get("Municipality", "") or address.get("District", "")

    def get_normalize_neighbourhood(self, data: dict[str, Any]) -> str:
        location = data.get("Location", {})
        address = location.get("Address", {})
        return address.get("Subdistrict", "") or address.get("Neighborhood", "")

    def get_normalize_city(self, data: dict[str, Any]) -> str:
        location = data.get("Location", {})
        address = location.get("Address", {})
        return address.get("City", "") or ""

    def get_normalize_postal_code(self, data: dict[str, Any]) -> str:
        location = data.get("Location", {})
        address = location.get("Address", {})
        return address.get("PostalCode", "") or ""

    def get_normalize_county(self, data: dict[str, Any]) -> str:
        location = data.get("Location", {})
        address = location.get("Address", {})
        return address.get("County", "") or ""

    def get_normalize_state(self, data: dict[str, Any]) -> str:
        location = data.get("Location", {})
        address = location.get("Address", {})
        return address.get("State", "") or ""

    def get_normalize_country_code(self, data: dict[str, Any]) -> str:
        location = data.get("Location", {})
        address = location.get("Address", {})
        country = address.get("Country", "")
        return country.upper() if country else ""

    def get_normalize_country(self, data: dict[str, Any]) -> str:
        location = data.get("Location", {})
        address = location.get("Address", {})
        return address.get("Country", "") or ""

    def search_addresses(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Search addresses using Here."""
        self.addresses_autocomplete_query = query
        kwargs.pop('raw', False)
        proximity = kwargs.pop('proximity', None)
        if not self._app_id or not self._app_code:
            raise ValueError("HERE_APP_ID and HERE_APP_CODE must be configured")

        params = {
            "app_id": self._app_id,
            "app_code": self._app_code,
            "searchtext": query,
            "maxresults": 10,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["prox"] = f"{lat},{lon},5000"

        response = requests.get(
            f"{self._base_url}/geocode.json",
            params=params,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        response_data = result.get("Response", {}) if isinstance(result, dict) else {}
        view = response_data.get("View", [])
        results_list = view[0].get("Result", []) if view else []
        return results_list if isinstance(results_list, list) else []

    def addresses_autocomplete(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Search addresses using Here."""
        self.addresses_autocomplete_query = query
        proximity = kwargs.pop('proximity', None)
        if not self._app_id or not self._app_code:
            raise ValueError("HERE_APP_ID and HERE_APP_CODE must be configured")

        params = {
            "app_id": self._app_id,
            "app_code": self._app_code,
            "searchtext": query,
            "maxresults": 10,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["prox"] = f"{lat},{lon},5000"

        response = requests.get(
            f"{self._base_url}/geocode.json",
            params=params,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        response_data = result.get("Response", {}) if isinstance(result, dict) else {}
        view = response_data.get("View", [])
        results_list = view[0].get("Result", []) if view else []
        return results_list if isinstance(results_list, list) else []

    def reverse_geocode(self, latitude: float | None = None, longitude: float | None = None, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Reverse geocode coordinates to an address using Here."""
        if latitude is None:
            latitude = kwargs.pop('latitude', None)
        if longitude is None:
            longitude = kwargs.pop('longitude', None)
        if latitude is None or longitude is None:
            raise ValueError("latitude and longitude are required")

        if not self._app_id or not self._app_code:
            raise ValueError("HERE_APP_ID and HERE_APP_CODE must be configured")

        self.reverse_geocode_latitude = latitude
        self.reverse_geocode_longitude = longitude

        params = {
            "app_id": self._app_id,
            "app_code": self._app_code,
            "prox": f"{latitude},{longitude},250",
            "mode": "retrieveAddresses",
            "maxresults": 1,
        }

        response = requests.get(
            f"{self._base_url}/geocode.json",
            params=params,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        response_data = result.get("Response", {}) if isinstance(result, dict) else {}
        view = response_data.get("View", [])
        results_list = view[0].get("Result", []) if view else []
        return results_list if isinstance(results_list, list) else []

