from __future__ import annotations

import time
from typing import Any

from .base import GeoaddressProvider

GEOCODE_EARTH_ADDRESSES_AUTOCOMPLETE_SOURCE = {
    'city': ['properties.locality', 'properties.localadmin', 'properties.county'],
    'postal_code': ['properties.postalcode'],
    'county': ['properties.county'],
    'state': ['properties.state'],
    'region': ['properties.region'],
    'country_code': ['properties.country_a'],
    'country': ['properties.country'],
    'municipality': ['properties.municipality'],
    'neighbourhood': ['properties.neighbourhood', 'properties.suburb', 'properties.district'],
    'address_type': ['properties.layer', 'properties.type'],
    'latitude': ['geometry.coordinates.1'],
    'longitude': ['geometry.coordinates.0'],
}


class GeocodeEarthProvider(GeoaddressProvider):
    name = "geocode_earth"
    display_name = "Geocode Earth"
    description = "Geocode Earth provider"
    required_packages = ["requests"]
    documentation_url = "https://geocode.earth/docs"
    site_url = "https://geocode.earth"
    config_keys = ["API_KEY", "BASE_URL"]
    config_defaults = {
        "BASE_URL": "https://api.geocode.earth/v1",
    }
    config_required = ["API_KEY"]
    cost_addresses_autocomplete = 0.00015
    cost_search_addresses = 0.00015
    cost_reverse_geocode = 0.00015

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize Geocode Earth provider."""
        super().__init__(**kwargs)
        self._base_url = self._get_config_or_env("BASE_URL", "https://api.geocode.earth/v1")
        api_key = self._get_config_or_env("API_KEY")
        self._api_key = api_key.strip() if api_key else None
        self._last_request_time = 0.0
        # Assign sources for each field (services_cfg is already copied by ProviderBase)
        for field, source in GEOCODE_EARTH_ADDRESSES_AUTOCOMPLETE_SOURCE.items():
            if field in self.services_cfg.get('addresses_autocomplete', {}).get('fields', {}):
                self.services_cfg['addresses_autocomplete']['fields'][field]['source'] = source
            if field in self.services_cfg.get('reverse_geocode', {}).get('fields', {}):
                self.services_cfg['reverse_geocode']['fields'][field]['source'] = source
            if field in self.services_cfg.get('search_addresses', {}).get('fields', {}):
                self.services_cfg['search_addresses']['fields'][field]['source'] = source

    def get_normalize_address_line1(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        address_line1_parts = []
        if properties.get("housenumber"):
            address_line1_parts.append(properties["housenumber"])
        if properties.get("street"):
            address_line1_parts.append(properties["street"])
        address_line1 = " ".join(address_line1_parts).strip()
        if not address_line1:
            address_line1 = properties.get("name", "")
        return address_line1 or ""

    def get_normalize_address_type(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        return properties.get("layer", "") or properties.get("type", "")

    def get_normalize_country_code(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        country_a = properties.get("country_a", "")
        return country_a.upper() if country_a else ""

    def search_addresses(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Search addresses using Geocode Earth."""
        self.addresses_autocomplete_query = query
        kwargs.pop('raw', False)
        proximity = kwargs.pop('proximity', None)
        if not self._api_key:
            raise ValueError("GEOCODE_EARTH_API_KEY not configured")

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.5:
            time.sleep(0.5 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "api_key": self._api_key,
            "text": query,
            "size": 10,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["focus.point.lat"] = str(lat)
            params["focus.point.lon"] = str(lon)

        response = requests.get(
            f"{self._base_url}/autocomplete",
            params=params,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        features = result.get("features", []) if isinstance(result, dict) else []
        return features if isinstance(features, list) else []

    def addresses_autocomplete(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Search addresses using Geocode Earth."""
        self.addresses_autocomplete_query = query
        proximity = kwargs.pop('proximity', None)
        if not self._api_key:
            raise ValueError("GEOCODE_EARTH_API_KEY not configured")

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.5:
            time.sleep(0.5 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "api_key": self._api_key,
            "text": query,
            "size": 10,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["focus.point.lat"] = str(lat)
            params["focus.point.lon"] = str(lon)

        response = requests.get(
            f"{self._base_url}/autocomplete",
            params=params,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        features = result.get("features", []) if isinstance(result, dict) else []
        return features if isinstance(features, list) else []

    def reverse_geocode(self, latitude: float | None = None, longitude: float | None = None, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Reverse geocode coordinates to an address using Geocode Earth."""
        if latitude is None:
            latitude = kwargs.pop('latitude', None)
        if longitude is None:
            longitude = kwargs.pop('longitude', None)
        if latitude is None or longitude is None:
            raise ValueError("latitude and longitude are required")

        if not self._api_key:
            raise ValueError("GEOCODE_EARTH_API_KEY not configured")

        self.reverse_geocode_latitude = latitude
        self.reverse_geocode_longitude = longitude

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.5:
            time.sleep(0.5 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "api_key": self._api_key,
            "point.lat": latitude,
            "point.lon": longitude,
        }

        response = requests.get(
            f"{self._base_url}/reverse",
            params=params,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        features = result.get("features", []) if isinstance(result, dict) else []
        return features if isinstance(features, list) else []

