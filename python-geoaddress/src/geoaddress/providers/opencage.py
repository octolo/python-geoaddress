from __future__ import annotations

from typing import Any

import requests

from .base import GeoaddressProvider

OPENCAGE_ADDRESSES_AUTOCOMPLETE_SOURCE = {
    'city': ['components.city', 'components.town', 'components.village'],
    'postal_code': ['components.postcode'],
    'county': ['components.county'],
    'state': ['components.state', 'components.state_district'],
    'region': ['components.region'],
    'country_code': ['components.country_code'],
    'country': ['components.country'],
    'municipality': ['components.municipality'],
    'neighbourhood': ['components.suburb', 'components.neighbourhood', 'components.quarter', 'components.district'],
    'address_type': ['components._type'],
    'latitude': ['geometry.lat'],
    'longitude': ['geometry.lng'],
    'number': ['components.house_number'],
    'street': ['components.road'],
}


class OpencageProvider(GeoaddressProvider):
    name = "opencage"
    display_name = "OpenCage"
    description = "OpenCage provider"
    required_packages = ["requests"]
    documentation_url = "https://opencagedata.com/api"
    site_url = "https://opencagedata.com"
    config_keys = ["API_KEY", "BASE_URL"]
    config_defaults = {
        "BASE_URL": "https://api.opencagedata.com/geocode/v1",
    }
    cost_addresses_autocomplete = 0.00017
    cost_search_addresses = 0.00017
    cost_reverse_geocode = 0.00017
    fields_associations = OPENCAGE_ADDRESSES_AUTOCOMPLETE_SOURCE

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize OpenCage provider."""
        super().__init__(**kwargs)
        self._base_url = self._get_config_or_env("BASE_URL", "https://api.opencagedata.com/geocode/v1")
        self._api_key = self._get_config_or_env("API_KEY")


    def get_normalize_address_line1(self, data: dict[str, Any]) -> str:
        components = data.get("components", {})
        house_number = components.get("house_number", "")
        road = components.get("road", "")
        if house_number and road:
            return f"{house_number} {road}".strip()
        if road:
            return road
        formatted = data.get("formatted", "")
        if formatted:
            parts = formatted.split(",")
            if parts:
                return parts[0].strip()
        return ""

    def get_normalize_city(self, data: dict[str, Any]) -> str:
        components = data.get("components", {})
        return components.get("city") or components.get("town") or components.get("village") or ""

    def get_normalize_postal_code(self, data: dict[str, Any]) -> str:
        components = data.get("components", {})
        return components.get("postcode") or ""

    def get_normalize_county(self, data: dict[str, Any]) -> str:
        components = data.get("components", {})
        return components.get("county") or ""

    def get_normalize_state(self, data: dict[str, Any]) -> str:
        components = data.get("components", {})
        return components.get("state") or components.get("state_district") or ""

    def get_normalize_region(self, data: dict[str, Any]) -> str:
        components = data.get("components", {})
        return components.get("region") or ""

    def get_normalize_country_code(self, data: dict[str, Any]) -> str:
        components = data.get("components", {})
        country_code = components.get("country_code", "")
        return country_code.upper() if country_code else ""

    def get_normalize_country(self, data: dict[str, Any]) -> str:
        components = data.get("components", {})
        return components.get("country") or ""

    def get_normalize_municipality(self, data: dict[str, Any]) -> str:
        components = data.get("components", {})
        return components.get("municipality") or ""

    def get_normalize_neighbourhood(self, data: dict[str, Any]) -> str:
        components = data.get("components", {})
        return (
            components.get("suburb")
            or components.get("neighbourhood")
            or components.get("quarter")
            or components.get("district")
            or ""
        )

    def search_addresses(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Search addresses using OpenCage."""
        self.addresses_autocomplete_query = query
        kwargs.pop('raw', False)
        proximity = kwargs.pop('proximity', None)
        if not self._api_key:
            raise ValueError("OPENCAGE_API_KEY not configured")

        params = {
            "key": self._api_key,
            "q": query,
            "limit": 10,
            "no_annotations": 0,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["proximity"] = f"{lat},{lon}"

        response = requests.get(
            f"{self._base_url}/json",
            params=params,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        results_list = result.get("results", []) if isinstance(result, dict) else []
        return results_list if isinstance(results_list, list) else []

    def addresses_autocomplete(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Search addresses using OpenCage."""
        self.addresses_autocomplete_query = query
        proximity = kwargs.pop('proximity', None)
        if not self._api_key:
            raise ValueError("OPENCAGE_API_KEY not configured")

        params = {
            "key": self._api_key,
            "q": query,
            "limit": 10,
            "no_annotations": 0,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["proximity"] = f"{lat},{lon}"

        response = requests.get(
            f"{self._base_url}/json",
            params=params,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        results_list = result.get("results", []) if isinstance(result, dict) else []
        return results_list if isinstance(results_list, list) else []

    def reverse_geocode(self, latitude: float | None = None, longitude: float | None = None, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Reverse geocode coordinates to an address using OpenCage."""
        if latitude is None:
            latitude = kwargs.pop('latitude', None)
        if longitude is None:
            longitude = kwargs.pop('longitude', None)
        if latitude is None or longitude is None:
            raise ValueError("latitude and longitude are required")

        if not self._api_key:
            raise ValueError("OPENCAGE_API_KEY not configured")

        self.reverse_geocode_latitude = latitude
        self.reverse_geocode_longitude = longitude

        params = {
            "key": self._api_key,
            "q": f"{latitude},{longitude}",
            "no_annotations": 0,
        }

        response = requests.get(
            f"{self._base_url}/json",
            params=params,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        results_list = result.get("results", []) if isinstance(result, dict) else []
        return results_list if isinstance(results_list, list) else []


