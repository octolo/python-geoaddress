from __future__ import annotations

import unicodedata
from math import atan2, cos, radians, sin, sqrt
from typing import TYPE_CHECKING, Any, cast

from providerkit import ProviderBase

from geoaddress import GEOADDRESS_FIELDS_DESCRIPTIONS, GEOADDRESS_FIELDS_FORMATS

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
    _default_services_cfg = {
        "search_addresses": {
            "label": "Search addresses",
            "description": "Search addresses",
            "format": "str",
            "fields": GEOADDRESS_FIELDS_DESCRIPTIONS
        },
        "reverse_geocode": {
            "label": "Reverse geocode",
            "description": "Reverse geocode",
            "format": "str",
            "fields": GEOADDRESS_FIELDS_DESCRIPTIONS
        },
    }
    geoaddress_timeout = 3
    provider_key = "key"
    importance_key = "importance"

    def insert_data_normalized(self, data_normalized: dict[str, Any] | list[dict[str, Any]]) -> dict[str, Any] | list[dict[str, Any]]:  # noqa: C901
        raw_result = None
        service_name = None
        if hasattr(self, '_service_results_cache') and self._service_results_cache:
            for svc_name, svc_data in self._service_results_cache.items():
                if 'result' in svc_data:
                    service_name = svc_name
                    raw_result = svc_data['result']
                    break

        if isinstance(data_normalized, list):
            raw_list = raw_result if isinstance(raw_result, list) else None
            for idx, item in enumerate(data_normalized):
                item["backend"] = self.display_name
                item["backend_name"] = self.name
                item["geoaddress_id"] = self._generate_geoaddress_id(item.get('latitude'), item.get('longitude'))
                item["text"] = self._build_address_string(item)
                for field_name, format_config in GEOADDRESS_FIELDS_FORMATS.items():
                    item[field_name] = self.insert_text_formatted(item, cast("list[Any]", format_config), field_name)

                feature = raw_list[idx] if raw_list and idx < len(raw_list) else None
                if not item.get('confidence'):
                    item['confidence'] = self._calculate_confidence(item, feature=feature, importance_key=self.importance_key)
                if not item.get('relevance'):
                    query_components = self._extract_query_components(raw_result, service_name)
                    query_lat = query_components.get('latitude')
                    query_lon = query_components.get('longitude')
                    item['relevance'] = self._calculate_relevance(query_components or {}, item, query_latitude=query_lat, query_longitude=query_lon)

        elif isinstance(data_normalized, dict):
            data_normalized["backend"] = self.display_name
            data_normalized["backend_name"] = self.name
            data_normalized["geoaddress_id"] = self._generate_geoaddress_id(data_normalized.get('latitude'), data_normalized.get('longitude'))
            data_normalized["text"] = self._build_address_string(data_normalized)
            for field_name, format_config in GEOADDRESS_FIELDS_FORMATS.items():
                data_normalized[field_name] = self.insert_text_formatted(data_normalized, cast("list[Any]", format_config), field_name)

            feature = raw_result if isinstance(raw_result, dict) else (raw_result[0] if isinstance(raw_result, list) and raw_result else None)
            if not data_normalized.get('confidence'):
                data_normalized['confidence'] = self._calculate_confidence(data_normalized, feature=feature, importance_key=self.importance_key)
            if not data_normalized.get('relevance'):
                query_components = self._extract_query_components(raw_result, service_name)
                query_lat = query_components.get('latitude')
                query_lon = query_components.get('longitude')
                data_normalized['relevance'] = self._calculate_relevance(query_components or {}, data_normalized, query_latitude=query_lat, query_longitude=query_lon)
        return data_normalized

    def _extract_query_components(self, raw_result: Any, service_name: str | None) -> dict[str, Any]:
        query_components: dict[str, Any] = {}
        if service_name == "search_addresses":
            query = getattr(self, 'search_addresses_query', None)
            if not query and isinstance(raw_result, list) and raw_result:
                first_item = raw_result[0] if raw_result else None
                if isinstance(first_item, dict):
                    query = first_item.get('query') or first_item.get('q') or first_item.get('display_name')
            if query:
                query_components['address_line1'] = str(query)
        elif service_name == "reverse_geocode":
            lat = getattr(self, 'reverse_geocode_latitude', None)
            lon = getattr(self, 'reverse_geocode_longitude', None)
            if lat is None or lon is None:
                lat = getattr(self, 'latitude', None)
                lon = getattr(self, 'longitude', None)
            if lat is not None and lon is not None:
                query_components['latitude'] = float(lat)
                query_components['longitude'] = float(lon)
        return query_components

    def insert_text_formatted(self, data_normalized: dict[str, Any], format_config: list[Any], _field_name: str) -> list[str] | list[list[str]]:
        result: list[Any] = []
        for item in format_config:
            if isinstance(item, list):
                group_parts = [str(data_normalized.get(field, "")) for field in item if data_normalized.get(field)]
                if group_parts:
                    result.append(group_parts)
            else:
                value = data_normalized.get(item)
                if value:
                    result.append(str(value))
        return result if result else []

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

        if can_calculate_distance and query_latitude is not None and query_longitude is not None:
            try:
                distance_km = self._calculate_distance_km(
                    query_latitude,
                    query_longitude,
                    float(normalized_result["latitude"]),
                    float(normalized_result["longitude"]),
                )
                distance_score = weights.get("distance", 0) * (1.0 / (distance_km + 1.0))
                score += distance_score
                max_score += weights.get("distance", 0)
            except (TypeError, ValueError):
                pass

        if max_score > 0:
            relevance_percent = min(100.0, max(0.0, (score / max_score) * 100.0))
        elif can_calculate_distance:
            relevance_percent = 100.0
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
                normalized.get("county"),
                normalized.get("state"),
                normalized.get("region"),
                normalized.get("country_code"),
            )
            if part
        ]
        return ", ".join(parts)

    def _parse_proximity(self, proximity: str | None) -> tuple[float | None, float | None]:
        """Parse proximity string to extract latitude and longitude."""
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

    def _generate_geoaddress_id(self, latitude: float | None, longitude: float | None) -> str:
        if latitude is None or longitude is None:
            return f"{self.name}-unknown"
        return f"{self.name}_{latitude}:{longitude}"
