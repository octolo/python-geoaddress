from __future__ import annotations

from typing import Any


class ConfidenceMixin:
    """Mixin for confidence calculation methods."""

    def _extract_importance(self, feature: dict[str, Any] | None, importance_key: str | None) -> float | None:
        """Extract importance value from feature."""
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
        """Calculate confidence from importance value."""
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
        """Calculate confidence using heuristic rules."""
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
        """Calculate confidence score for normalized address data."""
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
