from __future__ import annotations

import unicodedata
from math import atan2, cos, radians, sin, sqrt
from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from collections.abc import Callable


class RelevanceMixin:
    """Mixin for relevance calculation methods."""

    @staticmethod
    def _round_score(score: float) -> float:
        """Round score to 2 decimal places."""
        return round(score, 2)

    @staticmethod
    def _normalize_string_for_comparison(text: str | None) -> str:
        """Normalize string for comparison."""
        if not text:
            return ""
        normalized = " ".join(text.lower().strip().split())
        normalized = unicodedata.normalize("NFD", normalized)
        normalized = "".join(c for c in normalized if unicodedata.category(c) != "Mn")
        return normalized

    @staticmethod
    def _calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in kilometers."""
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c

    def _calculate_relevance_score(
        self,
        query_components: dict[str, Any],
        normalized_result: dict[str, Any],
        weights: dict[str, float],
    ) -> float:
        """Calculate relevance score based on query and result matching."""
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
            q_keys: list[str] = cast("list[str]", rule["query_key"]) if isinstance(rule["query_key"], list) else [cast("str", rule["query_key"])]
            r_keys: list[str] = cast("list[str]", rule["result_key"]) if isinstance(rule["result_key"], list) else [cast("str", rule["result_key"])]
            weight_key: str = cast("str", rule["weight_key"])
            match_type: str = cast("str", rule["match_type"])

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
        """Calculate relevance score for normalized address data."""
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

