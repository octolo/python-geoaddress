from __future__ import annotations

from typing import Any

import requests

from .base import GeoaddressProvider

MAPS_CO_ADDRESSES_AUTOCOMPLETE_SOURCE = {
    'city': ['address.city', 'address.town', 'address.village'],
    'postal_code': ['address.postcode'],
    'county': ['address.county'],
    'state': ['address.state', 'address.province'],
    'region': ['address.region'],
    'country_code': ['address.country_code'],
    'country': ['address.country'],
    'municipality': ['address.municipality'],
    'neighbourhood': ['address.neighbourhood', 'address.suburb', 'address.quarter'],
    'address_type': ['type', 'class'],
    'latitude': ['lat', 'centroid.coordinates.1', 'geometry.coordinates.1'],
    'longitude': ['lon', 'centroid.coordinates.0', 'geometry.coordinates.0'],
    'osm_id': ['osm_id'],
    'osm_type': ['osm_type'],
    'number': ['address.house_number', 'house_number'],
    'street': ['address.road', 'address.street', 'road', 'street'],
}


class MapsCoProvider(GeoaddressProvider):
    name = "maps_co"
    display_name = "Maps.co"
    description = "Maps.co provider"
    required_packages = ["requests"]
    documentation_url = "https://geocode.maps.co/docs/"
    site_url = "https://geocode.maps.co"
    config_keys = ["API_KEY", "BASE_URL"]
    config_defaults = {
        "BASE_URL": "https://geocode.maps.co",
    }
    priority = 5
    fields_associations = MAPS_CO_ADDRESSES_AUTOCOMPLETE_SOURCE

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize Maps.co provider."""
        super().__init__(**kwargs)
        self._base_url = self._get_config_or_env("BASE_URL", "https://geocode.maps.co")
        self._api_key = self._get_config_or_env("API_KEY")

    def get_normalize_address_type(self, data: dict[str, Any]) -> str:
        return (
            (data.get("type")
                if data.get("class") in ("place", "highway")
                else (data.get("type") or "building")
                if data.get("class") == "building"
                else (f"{data.get('class')}_{data.get('type')}" if data.get("type") else data.get("class"))
            )
            if data.get("class") and data.get("type")
            else (data.get("class") or data.get("type") or "")
        )

    def get_normalize_address_line1(self, data: dict[str, Any]) -> str:
        src_hn = ['house_number', 'address.house_number', 'addresstags.house_number']
        src_rd = ['street', 'road', 'address.road', 'addresstags.street']
        house_number = self._normalize_recursive(data, 'address_line1', src_hn)
        road = self._normalize_recursive(data, 'address_line1', src_rd)
        return f'{house_number} {road}'.strip()

    def get_normalize_city(self, data: dict[str, Any]) -> str:
        address = data.get("address", {})
        return address.get("city") or address.get("town") or address.get("village") or ""

    def get_normalize_postal_code(self, data: dict[str, Any]) -> str:
        address = data.get("address", {})
        return address.get("postcode") or ""

    def get_normalize_county(self, data: dict[str, Any]) -> str:
        address = data.get("address", {})
        return address.get("county") or ""

    def get_normalize_state(self, data: dict[str, Any]) -> str:
        address = data.get("address", {})
        return address.get("state") or address.get("province") or ""

    def get_normalize_region(self, data: dict[str, Any]) -> str:
        address = data.get("address", {})
        return address.get("region") or ""

    def get_normalize_country_code(self, data: dict[str, Any]) -> str:
        address = data.get("address", {})
        country_code = address.get("country_code", "")
        return country_code.upper() if country_code else ""

    def get_normalize_country(self, data: dict[str, Any]) -> str:
        address = data.get("address", {})
        return address.get("country") or ""

    def get_normalize_municipality(self, data: dict[str, Any]) -> str:
        address = data.get("address", {})
        return address.get("municipality") or ""

    def get_normalize_neighbourhood(self, data: dict[str, Any]) -> str:
        address = data.get("address", {})
        return (
            address.get("neighbourhood")
            or address.get("suburb")
            or address.get("quarter")
            or ""
        )

    def search_addresses(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Search addresses using Maps.co."""
        self.addresses_autocomplete_query = query
        kwargs.pop('raw', False)
        proximity = kwargs.pop('proximity', None)
        if not self._api_key:
            raise ValueError("MAPS_CO_API_KEY not configured")

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

        response = requests.get(f"{self._base_url}/search", params=params, timeout=self.geoaddress_timeout)
        response.raise_for_status()
        return response.json()

    def addresses_autocomplete(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Search addresses using Maps.co."""
        self.addresses_autocomplete_query = query
        proximity = kwargs.pop('proximity', None)
        if not self._api_key:
            raise ValueError("MAPS_CO_API_KEY not configured")

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

        response = requests.get(f"{self._base_url}/search", params=params, timeout=self.geoaddress_timeout)
        response.raise_for_status()
        return response.json()

    def reverse_geocode(self, latitude: float | None = None, longitude: float | None = None, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Reverse geocode coordinates to an address using Maps.co."""
        if latitude is None:
            latitude = kwargs.pop('latitude', None)
        if longitude is None:
            longitude = kwargs.pop('longitude', None)
        if latitude is None or longitude is None:
            raise ValueError("latitude and longitude are required")

        if not self._api_key:
            raise ValueError("MAPS_CO_API_KEY not configured")

        self.reverse_geocode_latitude = latitude
        self.reverse_geocode_longitude = longitude

        params = {
            "api_key": self._api_key,
            "lat": str(latitude),
            "lon": str(longitude),
            "format": "json",
            "addressdetails": 1,
        }

        response = requests.get(f"{self._base_url}/reverse", params=params, timeout=self.geoaddress_timeout)
        response.raise_for_status()
        result = response.json()
        if isinstance(result, dict):
            return [result]
        return result

