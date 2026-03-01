from __future__ import annotations

import urllib.parse
from typing import Any

import requests

from .base import GeoaddressProvider

MAPBOX_ADDRESSES_AUTOCOMPLETE_SOURCE = {
    'city': ['context.place'],
    'postal_code': ['context.postcode'],
    'county': ['context.county'],
    'state': ['context.region'],
    'region': ['context.region'],
    'country_code': ['context.country'],
    'country': ['context.country'],
    'municipality': ['context.district'],
    'neighbourhood': ['context.neighborhood'],
    'address_type': ['properties.type'],
    'latitude': ['geometry.coordinates.1'],
    'longitude': ['geometry.coordinates.0'],
    'number': ['properties.address_number'],
    'street': ['properties.street'],
}


class MapboxProvider(GeoaddressProvider):
    name = "mapbox"
    display_name = "Mapbox"
    description = "Mapbox provider"
    required_packages = ["requests"]
    documentation_url = "https://docs.mapbox.com/api/search/geocoding/"
    site_url = "https://www.mapbox.com"
    config_keys = ["ACCESS_TOKEN"]
    cost_addresses_autocomplete = 0.0005
    cost_search_addresses = 0.0005
    cost_reverse_geocode = 0.0005
    priority = 3
    fields_associations = MAPBOX_ADDRESSES_AUTOCOMPLETE_SOURCE

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize Mapbox provider."""
        super().__init__(**kwargs)
        self._base_url = "https://api.mapbox.com"
        self._access_token = self._get_config_or_env("ACCESS_TOKEN")


    def _extract_context_value(self, context: list[dict[str, Any]], prefix: str) -> str:
        """Extract value from context array by id prefix."""
        for item in context:
            item_id = item.get("id", "")
            if item_id.startswith(prefix):
                return str(item.get("text", ""))
        return ""

    def get_normalize_address_line1(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        address_line1 = properties.get("address", "")
        if address_line1:
            return address_line1
        place_name = data.get("place_name", "")
        if place_name:
            parts = place_name.split(",")
            if parts:
                return parts[0].strip()
        address_number = properties.get("address_number", "")
        street = properties.get("street", "")
        if address_number and street:
            return f"{address_number} {street}".strip()
        if street:
            return street
        text = data.get("text", "")
        return text if text else ""

    def get_normalize_city(self, data: dict[str, Any]) -> str:
        context = data.get("context", [])
        return self._extract_context_value(context, "place")

    def get_normalize_postal_code(self, data: dict[str, Any]) -> str:
        context = data.get("context", [])
        return self._extract_context_value(context, "postcode")

    def get_normalize_county(self, data: dict[str, Any]) -> str:
        context = data.get("context", [])
        return self._extract_context_value(context, "county")

    def get_normalize_state(self, data: dict[str, Any]) -> str:
        context = data.get("context", [])
        state = ""
        for item in context:
            item_id = item.get("id", "")
            if item_id.startswith("region"):
                region_text = item.get("text", "")
                if region_text and not state:
                    state = region_text
                    break
        return state

    def get_normalize_region(self, data: dict[str, Any]) -> str:
        context = data.get("context", [])
        regions = []
        for item in context:
            item_id = item.get("id", "")
            if item_id.startswith("region"):
                region_text = item.get("text", "")
                if region_text:
                    regions.append(region_text)
        return regions[-1] if len(regions) > 1 else ""

    def get_normalize_country_code(self, data: dict[str, Any]) -> str:
        context = data.get("context", [])
        for item in context:
            item_id = item.get("id", "")
            if item_id.startswith("country"):
                country_code = item.get("short_code", "")
                return country_code.upper() if country_code else ""
        return ""

    def get_normalize_country(self, data: dict[str, Any]) -> str:
        context = data.get("context", [])
        for item in context:
            item_id = item.get("id", "")
            if item_id.startswith("country"):
                return item.get("text", "") or ""
        return ""

    def get_normalize_municipality(self, data: dict[str, Any]) -> str:
        context = data.get("context", [])
        return self._extract_context_value(context, "district")

    def get_normalize_neighbourhood(self, data: dict[str, Any]) -> str:
        context = data.get("context", [])
        return self._extract_context_value(context, "neighborhood")

    def search_addresses(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Search addresses using Mapbox."""
        self.addresses_autocomplete_query = query
        kwargs.pop('raw', False)
        proximity = kwargs.pop('proximity', None)
        if not self._access_token:
            raise ValueError("MAPBOX_ACCESS_TOKEN not configured")

        encoded_query = urllib.parse.quote(query)
        params = {
            "access_token": self._access_token,
            "limit": 10,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["proximity"] = f"{lon},{lat}"

        response = requests.get(
            f"{self._base_url}/geocoding/v5/mapbox.places/{encoded_query}.json",
            params=params,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        features = result.get("features", []) if isinstance(result, dict) else []
        return features if isinstance(features, list) else []

    def addresses_autocomplete(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Search addresses using Mapbox."""
        self.addresses_autocomplete_query = query
        proximity = kwargs.pop('proximity', None)
        if not self._access_token:
            raise ValueError("MAPBOX_ACCESS_TOKEN not configured")

        encoded_query = urllib.parse.quote(query)
        params = {
            "access_token": self._access_token,
            "limit": 10,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["proximity"] = f"{lon},{lat}"

        response = requests.get(
            f"{self._base_url}/geocoding/v5/mapbox.places/{encoded_query}.json",
            params=params,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        features = result.get("features", []) if isinstance(result, dict) else []
        return features if isinstance(features, list) else []

    def reverse_geocode(self, latitude: float | None = None, longitude: float | None = None, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Reverse geocode coordinates to an address using Mapbox."""
        if latitude is None:
            latitude = kwargs.pop('latitude', None)
        if longitude is None:
            longitude = kwargs.pop('longitude', None)
        if latitude is None or longitude is None:
            raise ValueError("latitude and longitude are required")

        if not self._access_token:
            raise ValueError("MAPBOX_ACCESS_TOKEN not configured")

        self.reverse_geocode_latitude = latitude
        self.reverse_geocode_longitude = longitude

        params = {
            "access_token": self._access_token,
            "limit": 1,
        }

        response = requests.get(
            f"{self._base_url}/geocoding/v5/mapbox.places/{longitude},{latitude}.json",
            params=params,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        features = result.get("features", []) if isinstance(result, dict) else []
        return features if isinstance(features, list) else []

