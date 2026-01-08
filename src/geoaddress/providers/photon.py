from __future__ import annotations

import time
from typing import Any

from . import GeoaddressProvider


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
    config_required = []
    priority = 5

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize Photon provider."""
        super().__init__(**kwargs)
        self._base_url = self._get_config_or_env("BASE_URL", "https://photon.komoot.io")
        self._user_agent = self._get_config_or_env("USER_AGENT", "python-geoaddress/1.0")
        self._last_request_time = 0.0

    def _extract_address_from_feature(self, feature: dict[str, Any]) -> dict[str, Any]:  # noqa: C901

        """Extract address components from a Photon feature."""
        properties = feature.get("properties", {})

        address_line1 = ""
        house_number = properties.get("housenumber", "")
        street = properties.get("street", "")
        if house_number and street:
            address_line1 = f"{house_number} {street}".strip()
        elif street:
            address_line1 = street

        city = properties.get("city") or properties.get("town") or properties.get("village") or ""
        postal_code = properties.get("postcode", "")
        county = properties.get("county", "")
        state = properties.get("state", "")
        region = properties.get("region", "")
        country_code = properties.get("countrycode", "").upper()
        country = properties.get("country", "")

        municipality = properties.get("municipality", "")
        neighbourhood = (
            properties.get("district")
            or properties.get("suburb")
            or properties.get("quarter")
            or properties.get("neighbourhood")
            or ""
        )

        osm_key = properties.get("osm_key", "")
        osm_value = properties.get("osm_value", "")
        address_type = ""
        if osm_key and osm_value:
            if osm_key == "place" or osm_key == "highway":
                address_type = osm_value
            elif osm_key == "building":
                address_type = osm_value if osm_value else "building"
            else:
                address_type = f"{osm_key}_{osm_value}" if osm_value else osm_key
        elif osm_key:
            address_type = osm_key
        elif osm_value:
            address_type = osm_value

        coords = feature.get("geometry", {}).get("coordinates", [])
        reference = None
        if len(coords) >= 2:
            latitude = float(coords[1])
            longitude = float(coords[0])
            reference = f"{latitude}-{longitude}"

        osm_id = properties.get("osm_id")
        osm_type = properties.get("osm_type")

        return {
            "address_line1": address_line1,
            "address_line2": "",
            "address_line3": "",
            "city": city,
            "postal_code": postal_code,
            "county": county,
            "state": state,
            "region": region,
            "country_code": country_code,
            "country": country,
            "municipality": municipality,
            "neighbourhood": neighbourhood,
            "address_type": address_type,
            "reference": reference,
            "osm_id": int(osm_id) if osm_id is not None else None,
            "osm_type": osm_type if osm_type else None,
        }

    def search_addresses(self, query: str, *args: Any, **kwargs: Any) -> list[dict[str, Any]]:  # noqa: C901
        """Search addresses using Photon."""
        raw = kwargs.pop('raw', False)
        proximity = kwargs.pop('proximity', None)
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.1:
            time.sleep(0.1 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "q": query,
            "limit": 10,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["lat"] = str(lat)
            params["lon"] = str(lon)

        headers = {"User-Agent": self._user_agent}

        try:
            response = requests.get(
                f"{self._base_url}/api",
                params=params,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()

            if raw:
                features = result.get("features", []) if isinstance(result, dict) else []
                return features if isinstance(features, list) else []

            if isinstance(result, dict) and "error" in result:
                return []

            features = result.get("features", []) if isinstance(result, dict) else []
            if not isinstance(features, list):
                return []

            addresses = []
            for feature in features:
                normalized = self._extract_address_from_feature(feature)

                coords = feature.get("geometry", {}).get("coordinates", [])
                if len(coords) >= 2:
                    normalized["longitude"] = float(coords[0])
                    normalized["latitude"] = float(coords[1])

                normalized["backend"] = self.display_name
                normalized["backend_name"] = self.name
                normalized["text"] = self._build_address_string(normalized)
                normalized["confidence"] = self._calculate_confidence(
                    normalized,
                    feature=feature,
                    importance_key="properties.importance",
                )
                normalized["relevance"] = self._calculate_relevance(
                    {"address_line1": query},
                    normalized,
                )
                normalized["geoaddress_id"] = self._generate_geoaddress_id(normalized)
                normalized = self._order_normalized_fields(normalized)
                addresses.append(normalized)

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

        """Reverse geocode coordinates to an address using Photon."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.1:
            time.sleep(0.1 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "lat": str(latitude),
            "lon": str(longitude),
            "limit": 1,
        }

        headers = {"User-Agent": self._user_agent}

        try:
            response = requests.get(
                f"{self._base_url}/reverse",
                params=params,
                headers=headers,
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()

            if raw:
                features = result.get("features", []) if isinstance(result, dict) else []
                return features[0] if features else None

            if isinstance(result, dict) and "error" in result:
                return None

            features = result.get("features", []) if isinstance(result, dict) else []
            if not features:
                return None

            feature = features[0]
            normalized = self._extract_address_from_feature(feature)

            coords = feature.get("geometry", {}).get("coordinates", [])
            if len(coords) >= 2:
                normalized["longitude"] = float(coords[0])
                normalized["latitude"] = float(coords[1])

            normalized["backend"] = self.display_name
            normalized["backend_name"] = self.name
            normalized["text"] = self._build_address_string(normalized)
            normalized["confidence"] = self._calculate_confidence(
                normalized,
                feature=feature,
                importance_key="properties.importance",
            )
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

    def get_address_by_reference(self, reference: str, raw: bool = False) -> dict[str, Any] | None:
        """Get address by reference (latitude-longitude) using reverse geocoding."""
        return self.get_address_by_reference_latlon(reference, raw=raw)


