from typing import Any, cast


class ConfidenceMixin:
    """Mixin for confidence calculation methods."""

    @staticmethod
    def _round_score(score: float) -> float:
        """Round score to 2 decimal places."""
        return round(score, 2)

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
        return cast("float", val)

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

    def _calculate_confidence_heuristic(self, data: Any, config: dict[str, Any]) -> float:
        """Calculate confidence using heuristic rules."""
        if isinstance(data, dict) and config and 'fields' in config:
            cfg = config.get('fields', {})
            normalize_func = getattr(self, '_normalize_recursive', lambda d, f, _s: d.get(f) if isinstance(d, dict) else None)
            address_line1 = normalize_func(data, 'address_line1', cfg.get('address_line1', {}).get('source')) or ""
            city = normalize_func(data, 'city', cfg.get('city', {}).get('source')) or ""
            postal_code = normalize_func(data, 'postal_code', cfg.get('postal_code', {}).get('source')) or ""
        elif isinstance(data, dict):
            address_line1 = data.get("address_line1") or ""
            city = data.get("city") or ""
            postal_code = data.get("postal_code") or ""
        else:
            address_line1 = ""
            city = ""
            postal_code = ""

        if address_line1 and any(c.isdigit() for c in str(address_line1)):
            return 90.0
        if address_line1:
            return 70.0
        if city or postal_code:
            return 50.0
        return 30.0

    def _calculate_confidence(
        self,
        normalized: dict[str, Any] | None = None,
        feature: dict[str, Any] | None = None,
        importance_key: str | None = None,
        importance_multiplier: float = 2.0,
        data: Any = None,
        config: dict[str, Any] | None = None,
    ) -> float:
        """Calculate confidence score for normalized address data."""
        if feature is None and data is not None:
            feature = data if isinstance(data, dict) else None

        importance = self._extract_importance(feature, importance_key)
        if importance is None and feature:
            importance = feature.get("importance") or feature.get("properties", {}).get("importance")

        if importance is not None:
            confidence = self._calculate_confidence_from_importance(importance, importance_multiplier)
            if confidence is not None:
                return confidence

        if data is not None and config is not None:
            base_conf = self._calculate_confidence_heuristic(data, config)
        elif normalized is not None:
            base_conf = self._calculate_confidence_heuristic(normalized, {})
        else:
            base_conf = 30.0
        return self._round_score(base_conf)

