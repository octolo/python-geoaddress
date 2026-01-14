from __future__ import annotations

from typing import Any

from . import GeoaddressProvider

NOMINATIM_SEARCH_ADDRESSES_SOURCE = {
    'city': ['address.city', 'address.town', 'address.village'],
    'postal_code': ['address.postcode'],
    'county': ['address.county', 'county'],
    'state': ['address.state', 'address.province'],
    'region': ['address.region'],
    'country_code': ['address.country_code'],
    'country': ['address.country'],
    'municipality': ['address.municipality'],
    'neighbourhood': ['address.neighbourhood', 'address.suburb', 'address.quarter'],
    'address_type': ['type', 'class'],
    'latitude': ['lat' , 'centroid.coordinates.1', 'geometry.coordinates.1'],
    'longitude': ['lon' , 'centroid.coordinates.0', 'geometry.coordinates.0'],
    'osm_id': ['osm_id'],
    'osm_type': ['osm_type'],
}

NOMINATIM_CONFIG_FIELDS = {
    'country_code': 'country_code',
    'city': 'city',
    'postal_code': 'postal_code',
    'county': '',
    'state': 'state',
    'region': 'region',
    'country': 'country',
    'municipality': 'administrative',
    'neighbourhood': 'neighbourhood',
    'address_type': 'address_type',
    'latitude': 'latitude',
    'longitude': 'longitude',
    'osm_id': 'osm_id',
    'osm_type': 'osm_type',
}


class NominatimProvider(GeoaddressProvider):
    name = "nominatim"
    display_name = "Nominatim"
    description = "Nominatim provider"
    required_packages = ["requests"]
    documentation_url = "https://nominatim.org/release-docs/develop/api/Overview/"
    site_url = "https://nominatim.org"
    config_keys = ["BASE_URL", "USER_AGENT"]
    config_defaults = {
        "BASE_URL": "https://nominatim.openstreetmap.org",
        "USER_AGENT": "python-geoaddress/1.0",
    }
    config_required = ["USER_AGENT"]

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize Nominatim provider."""
        super().__init__(**kwargs)
        self._base_url = self._get_config_or_env("BASE_URL", "https://nominatim.openstreetmap.org")
        self._user_agent = self._get_config_or_env("USER_AGENT", "python-geoaddress/1.0")
        self._last_request_time = 0.0
        for field, source in NOMINATIM_SEARCH_ADDRESSES_SOURCE.items():
            self.services_cfg['search_addresses']['fields'][field]['source'] = source
            self.services_cfg['reverse_geocode']['fields'][field]['source'] = source

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

    def search_addresses(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Search addresses using Nominatim."""
        self.search_addresses_query = query
        kwargs.pop('raw', False)
        proximity = kwargs.pop('proximity', None)
        params = {"q": query, "format": "json", "addressdetails": 1, "limit": 10,}
        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["lat"] = str(lat)
            params["lon"] = str(lon)

        headers = {"User-Agent": self._user_agent}
        response = requests.get(
            f"{self._base_url}/search",
            params=params,
            headers=headers,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        return response.json()

    def reverse_geocode(self, latitude: float | None = None, longitude: float | None = None, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901, ARG002
        """Reverse geocode coordinates to an address using Nominatim."""
        if latitude is None:
            latitude = kwargs.pop('latitude', None)
        if longitude is None:
            longitude = kwargs.pop('longitude', None)
        if latitude is None or longitude is None:
            raise ValueError("latitude and longitude are required")

        self.reverse_geocode_latitude = latitude
        self.reverse_geocode_longitude = longitude

        params = {"lat": str(latitude), "lon": str(longitude), "format": "json", "addressdetails": 1}
        headers = {"User-Agent": self._user_agent}
        response = requests.get(
            f"{self._base_url}/reverse",
            params=params,
            headers=headers,
            timeout=self.geoaddress_timeout,
        )
        response.raise_for_status()
        result = response.json()
        if isinstance(result, dict):
            return [result]
        return result

