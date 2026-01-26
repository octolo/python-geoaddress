from __future__ import annotations

from typing import Any

import requests

from .base import GeoaddressProvider

PHOTON_ADDRESSES_AUTOCOMPLETE_SOURCE = {
    'city': ['properties.city', 'properties.town', 'properties.village'],
    'postal_code': ['properties.postcode'],
    'county': ['properties.county'],
    'state': ['properties.state'],
    'region': ['properties.region'],
    'country_code': ['properties.countrycode'],
    'country': ['properties.country'],
    'municipality': ['properties.municipality'],
    'neighbourhood': ['properties.district', 'properties.suburb', 'properties.quarter', 'properties.neighbourhood'],
    'address_type': ['properties.osm_key', 'properties.osm_value'],
    'latitude': ['geometry.coordinates.1'],
    'longitude': ['geometry.coordinates.0'],
    'osm_id': ['properties.osm_id'],
    'osm_type': ['properties.osm_type'],
    'number': ['properties.housenumber'],
    'street': ['properties.street'],
}


class PhotonProvider(GeoaddressProvider):
    name = "photon"
    display_name = "Photon"
    description = "Photon provider"
    required_packages = ["requests"]
    documentation_url = "https://photon.komoot.io/docs"
    site_url = "https://photon.komoot.io"
    config_keys = ["BASE_URL", "USER_AGENT"]
    config_defaults = {
        "BASE_URL": "https://photon.komoot.io",
        "USER_AGENT": "python-geoaddress/1.0",
    }
    priority = 5
    fields_associations = PHOTON_ADDRESSES_AUTOCOMPLETE_SOURCE

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize Photon provider."""
        super().__init__(**kwargs)
        self._base_url = self._get_config_or_env("BASE_URL", "https://photon.komoot.io")
        self._user_agent = self._get_config_or_env("USER_AGENT", "python-geoaddress/1.0")

    def get_normalize_address_type(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        osm_key = properties.get("osm_key", "")
        osm_value = properties.get("osm_value", "")
        if osm_key and osm_value:
            if osm_key in ("place", "highway"):
                return osm_value
            if osm_key == "building":
                return osm_value if osm_value else "building"
            return f"{osm_key}_{osm_value}" if osm_value else osm_key
        if osm_key:
            return osm_key
        if osm_value:
            return osm_value
        return ""

    def get_normalize_address_line1(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        house_number = properties.get("housenumber", "")
        street = properties.get("street", "")
        if house_number and street:
            return f"{house_number} {street}".strip()
        if street:
            return street
        return ""

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
        return properties.get("state") or ""

    def get_normalize_region(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        return properties.get("region") or ""

    def get_normalize_country_code(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        countrycode = properties.get("countrycode", "")
        return countrycode.upper() if countrycode else ""

    def get_normalize_country(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        return properties.get("country") or ""

    def get_normalize_municipality(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        return properties.get("municipality") or ""

    def get_normalize_neighbourhood(self, data: dict[str, Any]) -> str:
        properties = data.get("properties", {})
        return (
            properties.get("district")
            or properties.get("suburb")
            or properties.get("quarter")
            or properties.get("neighbourhood")
            or ""
        )

    def get_normalize_osm_id(self, data: dict[str, Any]) -> int | None:
        properties = data.get("properties", {})
        osm_id = properties.get("osm_id")
        return int(osm_id) if osm_id is not None else None

    def search_addresses(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Search addresses using Photon."""
        self.addresses_autocomplete_query = query
        kwargs.pop('raw', False)
        proximity = kwargs.pop('proximity', None)
        params = {
            "q": query,
            "limit": 10,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["lat"] = str(lat)
            params["lon"] = str(lon)

        headers = {"User-Agent": self._user_agent}
        response = requests.get(
            f"{self._base_url}/api",
            params=params,
            headers=headers,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        features = result.get("features", []) if isinstance(result, dict) else []
        return features if isinstance(features, list) else []

    def addresses_autocomplete(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Search addresses using Photon."""
        self.addresses_autocomplete_query = query
        proximity = kwargs.pop('proximity', None)
        params = {
            "q": query,
            "limit": 10,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["lat"] = str(lat)
            params["lon"] = str(lon)

        headers = {"User-Agent": self._user_agent}
        response = requests.get(
            f"{self._base_url}/api",
            params=params,
            headers=headers,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        features = result.get("features", []) if isinstance(result, dict) else []
        return features if isinstance(features, list) else []

    def reverse_geocode(self, latitude: float | None = None, longitude: float | None = None, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Reverse geocode coordinates to an address using Photon."""
        if latitude is None:
            latitude = kwargs.pop('latitude', None)
        if longitude is None:
            longitude = kwargs.pop('longitude', None)
        if latitude is None or longitude is None:
            raise ValueError("latitude and longitude are required")

        self.reverse_geocode_latitude = latitude
        self.reverse_geocode_longitude = longitude

        params = {
            "lat": str(latitude),
            "lon": str(longitude),
            "limit": 1,
        }

        headers = {"User-Agent": self._user_agent}
        response = requests.get(
            f"{self._base_url}/reverse",
            params=params,
            headers=headers,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        features = result.get("features", []) if isinstance(result, dict) else []
        return features if isinstance(features, list) else []



