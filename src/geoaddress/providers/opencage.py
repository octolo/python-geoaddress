from __future__ import annotations

import time
from typing import Any

from . import GeoaddressProvider


class OpencageProvider(GeoaddressProvider):
    name = "opencage"
    display_name = "OpenCage"
    description = "OpenCage provider"
    required_packages = ["requests"]
    documentation_url = "https://opencagedata.com/api"
    site_url = "https://opencagedata.com"
    config_keys = ["OPENCAGE_API_KEY", "OPENCAGE_BASE_URL"]
    config_defaults = {
        "OPENCAGE_BASE_URL": "https://api.opencagedata.com/geocode/v1",
    }
    config_required = ["OPENCAGE_API_KEY"]

    def __init__(self, **kwargs: str | None) -> None:
        """Initialize OpenCage provider."""
        super().__init__(**kwargs)
        self._base_url = self._get_config_or_env("OPENCAGE_BASE_URL", "https://api.opencagedata.com/geocode/v1")
        self._api_key = self._get_config_or_env("OPENCAGE_API_KEY")
        self._last_request_time = 0.0

    def _extract_address_from_result(self, result: dict[str, Any]) -> dict[str, Any]:  # noqa: C901

        """Extract address components from an OpenCage result."""
        components = result.get("components", {})

        address_line1 = ""
        if components.get("house_number") and components.get("road"):
            address_line1 = f"{components.get('house_number')} {components.get('road')}".strip()
        elif components.get("road"):
            address_line1 = components.get("road", "")
        elif result.get("formatted"):
            formatted = result.get("formatted", "")
            parts = formatted.split(",")
            if parts:
                address_line1 = parts[0].strip()

        city = components.get("city") or components.get("town") or components.get("village") or ""
        municipality = components.get("municipality", "")
        state = components.get("state") or components.get("state_district") or ""
        region = components.get("region", "")

        neighbourhood = (
            components.get("suburb")
            or components.get("neighbourhood")
            or components.get("quarter")
            or components.get("district")
            or ""
        )

        address_type = components.get("_type", "")

        geometry = result.get("geometry", {})
        reference = None
        lat_val = geometry.get("lat")
        lon_val = geometry.get("lng")
        if lat_val is not None and lon_val is not None:
            reference = f"{float(lat_val)}-{float(lon_val)}"

        return {
            "address_line1": address_line1 or "",
            "address_line2": "",
            "address_line3": "",
            "city": city,
            "postal_code": components.get("postcode", ""),
            "state": state,
            "region": region,
            "country_code": (
                components.get("country_code", "").upper() if components.get("country_code") else ""
            ),
            "country": components.get("country", "") or "",
            "municipality": municipality,
            "neighbourhood": neighbourhood,
            "address_type": address_type,
            "reference": reference,
        }

    def search_addresses(self, query: str, raw: bool = False, proximity: str | None = None) -> list[dict[str, Any]]:  # noqa: C901

        """Search addresses using OpenCage."""
        if not self._api_key:
            if raw:
                return [{"error": "OPENCAGE_API_KEY not configured"}]
            return []

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.5:
            time.sleep(0.5 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "key": self._api_key,
            "q": query,
            "limit": 10,
            "no_annotations": 0,
        }

        lat, lon = self._parse_proximity(proximity)
        if lat is not None and lon is not None:
            params["proximity"] = f"{lat},{lon}"

        try:
            response = requests.get(
                f"{self._base_url}/json",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()

            if raw:
                results_list = result.get("results", []) if isinstance(result, dict) else []
                return results_list if isinstance(results_list, list) else []

            if isinstance(result, dict) and "error" in result:
                return []

            results_list = result.get("results", [])
            if not isinstance(results_list, list):
                return []

            addresses = []
            for item in results_list:
                try:
                    normalized = self._extract_address_from_result(item)

                    geometry = item.get("geometry", {})
                    lat_val = geometry.get("lat")
                    lon_val = geometry.get("lng")
                    if lat_val is not None:
                        normalized["latitude"] = float(lat_val)
                    if lon_val is not None:
                        normalized["longitude"] = float(lon_val)

                    if lat_val is not None and lon_val is not None:
                        normalized["reference"] = f"{float(lat_val)}-{float(lon_val)}"

                    normalized["backend"] = self.display_name
                    normalized["backend_name"] = self.name
                    normalized["text"] = self._build_address_string(normalized)

                    confidence_value = item.get("confidence", 0)
                    normalized["confidence"] = float(confidence_value) if confidence_value else 0.0
                    normalized["relevance"] = self._calculate_relevance(
                        {"address_line1": query},
                        normalized,
                    )
                    normalized["geoaddress_id"] = self._generate_geoaddress_id(normalized)
                    normalized = self._order_normalized_fields(normalized)
                    addresses.append(normalized)
                except Exception:
                    continue

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

        """Reverse geocode coordinates to an address using OpenCage."""
        if not self._api_key:
            if raw:
                return {"error": "OPENCAGE_API_KEY not configured"}
            return None

        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < 0.5:
            time.sleep(0.5 - time_since_last)
        self._last_request_time = time.time()

        params = {
            "key": self._api_key,
            "q": f"{latitude},{longitude}",
            "no_annotations": 0,
        }

        try:
            response = requests.get(
                f"{self._base_url}/json",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            result = response.json()

            if raw:
                results_list = result.get("results", []) if isinstance(result, dict) else []
                return results_list[0] if results_list else None

            if isinstance(result, dict) and "error" in result:
                return None

            results_list = result.get("results", [])
            if not results_list:
                return None

            item = results_list[0]
            normalized = self._extract_address_from_result(item)

            normalized["latitude"] = latitude
            normalized["longitude"] = longitude
            normalized["reference"] = f"{latitude}-{longitude}"

            normalized["backend"] = self.display_name
            normalized["backend_name"] = self.name
            normalized["text"] = self._build_address_string(normalized)

            confidence_value = item.get("confidence", 0)
            normalized["confidence"] = float(confidence_value) if confidence_value else 0.0
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

