from __future__ import annotations

from typing import Any

import requests

from .base import GeoaddressProvider

GEOAPIFY_ADDRESSES_AUTOCOMPLETE_SOURCE = {
    'city': ['properties.city', 'properties.town', 'properties.village'],
    'postal_code': ['properties.postcode'],
    'county': ['properties.county'],
    'state': ['properties.state', 'properties.state_code'],
    'region': ['properties.region'],
    'country_code': ['properties.country_code'],
    'country': ['properties.country'],
    'municipality': ['properties.municipality'],
    'neighbourhood': ['properties.neighbourhood', 'properties.suburb', 'properties.district', 'properties.quarter'],
    'address_type': ['properties.type', 'properties.category'],
    'latitude': ['properties.lat', 'geometry.coordinates.1'],
    'longitude': ['properties.lon', 'geometry.coordinates.0'],
    'number': ['properties.housenumber'],
    'street': ['properties.street'],
}


class GeoapifyProvider(GeoaddressProvider):
    name = "geoapify"
    display_name = "Geoapify"
    description = "Geoapify provider"
    required_packages = ["requests"]
    documentation_url = "https://apidocs.geoapify.com/docs/geocoding/"
    site_url = "https://www.geoapify.com"
    config_keys = ["API_KEY", "BASE_URL"]
    config_defaults = {
        "BASE_URL": "https://api.geoapify.com/v1",
    }
    cost_addresses_autocomplete = 0.0002
    cost_search_addresses = 0.0002
    cost_reverse_geocode = 0.0002
    priority = 2
    fields_associations = GEOAPIFY_ADDRESSES_AUTOCOMPLETE_SOURCE

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize Geoapify provider."""
        super().__init__(**kwargs)
        self._base_url = self._get_config_or_env("BASE_URL", "https://api.geoapify.com/v1")
        self._api_key = self._get_config_or_env("API_KEY")

    def get_normalize_address_line1(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        address_line1 = properties.get("address_line1", "")
        if address_line1:
            return address_line1
        address_line1_parts = []
        if properties.get("housenumber"):
            address_line1_parts.append(str(properties["housenumber"]))
        if properties.get("street"):
            address_line1_parts.append(properties["street"])
        return " ".join(address_line1_parts).strip()

    def get_normalize_address_type(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        return properties.get("type", "") or properties.get("category", "")

    def get_normalize_city(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        return properties.get("city") or properties.get("town") or properties.get("village") or ""

    def get_normalize_postal_code(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        return properties.get("postcode") or ""

    def get_normalize_county(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        return properties.get("county") or ""

    def get_normalize_state(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        return properties.get("state") or properties.get("state_code") or ""

    def get_normalize_region(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        return properties.get("region") or ""

    def get_normalize_country_code(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        country_code = properties.get("country_code", "")
        return country_code.upper() if country_code else ""

    def get_normalize_country(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        return properties.get("country") or ""

    def get_normalize_municipality(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        return properties.get("municipality") or ""

    def get_normalize_neighbourhood(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        return (
            properties.get("neighbourhood")
            or properties.get("suburb")
            or properties.get("district")
            or properties.get("quarter")
            or ""
        )

    def search_addresses(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Search addresses using Geoapify."""
        self.addresses_autocomplete_query = query
        proximity = kwargs.pop('proximity', None)
        if not self._api_key:
            raise ValueError("API_KEY not configured")

        params = {
            "apiKey": self._api_key,
            "text": query,
            "limit": 10,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["bias"] = f"proximity:{lon},{lat}"

        response = requests.get(
            f"{self._base_url}/geocode/search",
            params=params,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        features = result.get("features", []) if isinstance(result, dict) else []
        return features if isinstance(features, list) else []

    def addresses_autocomplete(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Autocomplete addresses using Geoapify."""
        self.addresses_autocomplete_query = query
        proximity = kwargs.pop('proximity', None)
        if not self._api_key:
            raise ValueError("API_KEY not configured")

        params = {
            "apiKey": self._api_key,
            "text": query,
            "limit": 10,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["bias"] = f"proximity:{lon},{lat}"

        response = requests.get(
            f"{self._base_url}/geocode/search",
            params=params,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        features = result.get("features", []) if isinstance(result, dict) else []
        return features if isinstance(features, list) else []

    def reverse_geocode(self, latitude: float | None = None, longitude: float | None = None, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Reverse geocode coordinates to an address using Geoapify."""
        if latitude is None:
            latitude = kwargs.pop('latitude', None)
        if longitude is None:
            longitude = kwargs.pop('longitude', None)
        if latitude is None or longitude is None:
            raise ValueError("latitude and longitude are required")

        if not self._api_key:
            raise ValueError("API_KEY not configured")

        self.reverse_geocode_latitude = latitude
        self.reverse_geocode_longitude = longitude

        params = {
            "apiKey": self._api_key,
            "lat": latitude,
            "lon": longitude,
        }

        response = requests.get(
            f"{self._base_url}/geocode/reverse",
            params=params,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        features = result.get("features", []) if isinstance(result, dict) else []
        return features if isinstance(features, list) else []


