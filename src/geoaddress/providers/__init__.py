from __future__ import annotations

import re
import unicodedata
from math import atan2, cos, radians, sin, sqrt
from typing import TYPE_CHECKING, Any

from providerkit import ProviderBase

from geoaddress import GEOADDRESS_FIELDS_DESCRIPTIONS

if TYPE_CHECKING:
    from collections.abc import Callable


class GeoaddressProvider(ProviderBase):
    fields_descriptions = GEOADDRESS_FIELDS_DESCRIPTIONS
    name = "geoaddress"
    display_name = "Geoaddress"
    description = "Geoaddress provider"
    required_packages = ["geoaddress"]
    documentation_url = "https://geoaddress.readthedocs.io"
    site_url = "https://geoaddress.readthedocs.io"
    config_keys: list[str] = []
    config_defaults: dict[str, Any] = {}
    config_required: list[str] = []
    config_prefix = "GEOADDRESS"
    services = ["search_addresses", "get_address_by_reference", "reverse_geocode", "get_address_by_osm"]

    @staticmethod
    def _round_score(score: float, decimals: int = 2) -> float:
        return round(float(score), decimals)

    @staticmethod
    def _normalize_string_for_comparison(text: str | None) -> str:
        if not text:
            return ""
        normalized = " ".join(text.lower().strip().split())
        normalized = unicodedata.normalize("NFD", normalized)
        normalized = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
        return normalized

    @staticmethod
    def _calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def _get_nested_value(self, data: dict[str, Any], path: str, default: Any = None) -> Any:
        """Get nested value from dict using dot notation path."""
        if not path:
            return default
        keys = path.split(".")
        val: Any = data
        for k in keys:
            if not isinstance(val, dict):
                return default
            val = val.get(k)
            if val is None:
                return default
        return val

    def _extract_importance(self, feature: dict[str, Any] | None, importance_key: str | None) -> float | None:
        if not feature or not importance_key:
            return None

        keys = importance_key.split(".")
        val: Any = feature
        for k in keys:
            val = val.get(k) if isinstance(val, dict) else None
            if val is None:
                return None
        return val  # type: ignore[no-any-return]

    def _calculate_confidence_from_importance(self, importance: float, multiplier: float) -> float | None:
        try:
            if isinstance(importance, dict):
                return None
            importance_val = float(importance)
            confidence = min(importance_val * multiplier, 1.0)
            if confidence >= 0.3:
                return self._round_score(max(0.0, confidence) * 100.0)
        except (ValueError, TypeError):
            pass
        return None

    def _calculate_confidence_heuristic(self, normalized: dict[str, Any]) -> float:
        address_line1 = normalized.get("address_line1") or ""
        city = normalized.get("city") or ""
        postal_code = normalized.get("postal_code") or ""

        if address_line1 and any(c.isdigit() for c in address_line1):
            return 90.0
        if address_line1:
            return 70.0
        if city or postal_code:
            return 50.0
        return 30.0

    def _calculate_confidence(
        self,
        normalized: dict[str, Any],
        feature: dict[str, Any] | None = None,
        importance_key: str | None = None,
        importance_multiplier: float = 2.0,
    ) -> float:
        if not isinstance(normalized, dict):
            normalized = {}

        importance = self._extract_importance(feature, importance_key)
        if importance is None and feature:
            importance = feature.get("importance") or feature.get("properties", {}).get("importance")

        if importance is not None:
            confidence = self._calculate_confidence_from_importance(importance, importance_multiplier)
            if confidence is not None:
                return confidence

        base_conf = self._calculate_confidence_heuristic(normalized)
        return self._round_score(base_conf)

    def _calculate_relevance_score(
        self,
        query_components: dict[str, Any],
        normalized_result: dict[str, Any],
        weights: dict[str, float],
    ) -> float:
        import re

        score = 0.0

        q_street = query_components.get("address_line1") or ""

        field_rules: list[dict[str, Any]] = [
            {
                "query_key": "address_line1",
                "result_key": "address_line1",
                "weight_key": "street",
                "extract_from_query": None,
                "match_type": "partial",
            },
            {
                "query_key": "postal_code",
                "result_key": "postal_code",
                "weight_key": "postcode",
                "extract_from_query": lambda: (match.group(0) if q_street and (match := re.search(r"\b\d{5}\b", q_street)) else ""),
                "match_type": "partial",
            },
            {
                "query_key": ["city", "village", "town", "municipality"],
                "result_key": ["city", "village", "town", "municipality"],
                "weight_key": "city",
                "extract_from_query": None,
                "match_type": "bidirectional",
            },
        ]

        for rule in field_rules:
            q_keys: list[str] = rule["query_key"] if isinstance(rule["query_key"], list) else [rule["query_key"]]  # type: ignore[assignment]
            r_keys: list[str] = rule["result_key"] if isinstance(rule["result_key"], list) else [rule["result_key"]]  # type: ignore[assignment]
            weight_key: str = rule["weight_key"]  # type: ignore[assignment]
            match_type: str = rule["match_type"]  # type: ignore[assignment]

            q_value = next((query_components.get(k) for k in q_keys if query_components.get(k)), "")
            extract_func: Callable[[], str] | None = rule.get("extract_from_query")
            if extract_func and not q_value:
                q_value = extract_func() or ""

            r_value = next((normalized_result.get(k) for k in r_keys if normalized_result.get(k)), "")

            if q_value and r_value:
                q_norm = self._normalize_string_for_comparison(q_value)
                r_norm = self._normalize_string_for_comparison(r_value)
                weight = weights.get(weight_key, 0)

                if match_type == "bidirectional":
                    if q_norm == r_norm or q_norm in r_norm or r_norm in q_norm:
                        score += weight
                else:
                    if q_norm == r_norm:
                        score += weight
                    elif r_norm in q_norm:
                        score += weight * 0.7

        return score

    def _calculate_relevance(
        self,
        query_components: dict[str, Any],
        normalized_result: dict[str, Any],
        query_latitude: float | None = None,
        query_longitude: float | None = None,
        weights: dict[str, float] | None = None,
        include_distance: bool = True,
    ) -> float:
        if weights is None:
            weights = {"street": 3.0, "postcode": 2.0, "city": 1.5, "distance": 1.0}

        score = self._calculate_relevance_score(query_components, normalized_result, weights)
        max_score = weights.get("street", 0) + weights.get("postcode", 0) + weights.get("city", 0)

        can_calculate_distance = (
            include_distance
            and query_latitude is not None
            and query_longitude is not None
            and normalized_result.get("latitude") is not None
            and normalized_result.get("longitude") is not None
        )

        if can_calculate_distance:
            max_score += weights.get("distance", 0)
            try:
                if query_latitude is not None and query_longitude is not None:
                    distance_km = self._calculate_distance_km(
                        query_latitude,
                        query_longitude,
                        float(normalized_result["latitude"]),
                        float(normalized_result["longitude"]),
                    )
                    distance_score = weights.get("distance", 0) * (1.0 / (distance_km + 1.0))
                    score += distance_score
            except (TypeError, ValueError):
                pass

        if max_score > 0:
            relevance_percent = min(100.0, max(0.0, (score / max_score) * 100.0))
        else:
            relevance_percent = 0.0
        return self._round_score(relevance_percent)

    def _build_address_string(self, normalized: dict[str, Any]) -> str:
        """Join address components into a single formatted string."""
        parts = [
            part
            for part in (
                normalized.get("address_line1"),
                normalized.get("address_line2"),
                normalized.get("address_line3"),
                normalized.get("city"),
                normalized.get("postal_code"),
                normalized.get("state"),
                normalized.get("country_code"),
            )
            if part
        ]
        return ", ".join(parts)

    def _normalize_from_mapping(self, data: dict[str, Any], mapping: dict[str, str | Any]) -> dict[str, Any]:
        """Normalize data using field mapping. Mapping values can be paths (str with dots), callables, or constants."""
        normalized: dict[str, Any] = {}
        for target_field in self.fields_descriptions:
            if target_field not in mapping:
                continue
            source = mapping[target_field]
            if callable(source):
                normalized[target_field] = source(data)
            elif isinstance(source, str) and "." in source:
                normalized[target_field] = self._get_nested_value(data, source)
            else:
                normalized[target_field] = source
        return normalized

    def _order_normalized_fields(self, normalized: dict[str, Any]) -> dict[str, Any]:
        """Reorder normalized fields according to fields_descriptions order."""
        ordered: dict[str, Any] = {}
        for field in self.fields_descriptions:
            if field in normalized:
                ordered[field] = normalized[field]
        return ordered

    def _parse_proximity(self, proximity: str | None) -> tuple[float | None, float | None]:
        """Parse proximity string to extract latitude and longitude.

        Args:
            proximity: Proximity string in format "lat,lon" (e.g., "2.3522,48.8566")

        Returns:
            Tuple of (latitude, longitude) or (None, None) if parsing fails.
        """
        if not proximity:
            return None, None

        try:
            parts = proximity.split(",")
            if len(parts) == 2:
                lat = float(parts[0].strip())
                lon = float(parts[1].strip())
                return lat, lon
        except (ValueError, AttributeError):
            pass

        return None, None

    def _generate_geoaddress_id(self, address: dict[str, Any]) -> str | None:
        reference = address.get("reference")
        backend_name = address.get("backend_name") or self.name
        if not reference or not backend_name:
            return None
        return f"{backend_name}-{reference}"

    def get_address_by_osm(self, _osm_keys_value: dict[str, Any], _raw: bool = False) -> list[dict[str, Any]] | None:  # noqa: C901
        """Get address by OSM key-value pairs.

        Args:
            osm_keys_value: Dictionary of OSM key-value pairs (e.g., {"place": "city", "name": "Paris"}).
            raw: If True, return raw provider response.

        Returns:
            List of normalized addresses or None if not implemented or error.
        """
        return None

    def get_address_by_reference_latlon(self, reference: str, raw: bool = False) -> dict[str, Any] | None:
        """Get address by reference (latitude-longitude) using reverse geocoding.

        This is a helper method for providers that use latitude-longitude format as reference.
        It parses the reference and calls reverse_geocode.

        Args:
            reference: Reference string in format "latitude-longitude" (e.g., "49.287724-2.494634").
            raw: If True, return raw provider response.

        Returns:
            Normalized address dictionary or None if error.
        """
        if not reference:
            if raw:
                return {"error": "Reference is required"}
            return None

        try:
            match = re.match(r"^(-?\d+\.?\d*)-(-?\d+\.?\d*)$", reference)
            if not match:
                if raw:
                    return {"error": "Invalid reference format. Expected 'latitude-longitude'"}
                return None

            latitude = float(match.group(1))
            longitude = float(match.group(2))
        except (ValueError, IndexError):
            if raw:
                return {"error": "Invalid latitude/longitude in reference"}
            return None

        result = self.reverse_geocode(latitude, longitude, raw=raw)
        return result if isinstance(result, dict) else None

