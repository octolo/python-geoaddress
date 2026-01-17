from __future__ import annotations

from typing import Any, cast

from providerkit import ProviderBase

from geoaddress import (
    GEOADDRESS_FIELDS_DESCRIPTIONS,
    GEOADDRESS_FIELDS_FORMATS,
    GEOADDRESS_FIELDS_SEARCH,
)

from .confidence import ConfidenceMixin
from .relevance import RelevanceMixin


class GeoaddressProvider(ProviderBase, ConfidenceMixin, RelevanceMixin):
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
            "fields": GEOADDRESS_FIELDS_SEARCH
        },
        "addresses_autocomplete": {
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

    # def get_backend_name(self, data_normalized: dict[str, Any]) -> dict[str, Any]:
    #     return self.display_name
#
    # def get_backend(self, data_normalized: dict[str, Any]) -> dict[str, Any]:
    #     return self.name
#
    # def insert_data_normalized(self, data_normalized: dict[str, Any] | list[dict[str, Any]], config: dict[str, Any] | None = None) -> dict[str, Any] | list[dict[str, Any]]:  # noqa: C901
    #     cfg = self.services_cfg.get(self.current_service_name, config)
    #     raw_result = None
    #     service_name = None
    #     if hasattr(self, '_service_results_cache') and self._service_results_cache:
    #         for svc_name, svc_data in self._service_results_cache.items():
    #             if 'result' in svc_data:
    #                 service_name = svc_name
    #                 raw_result = svc_data['result']
    #                 break
#
    #     if isinstance(data_normalized, list):
    #         raw_list = raw_result if isinstance(raw_result, list) else None
    #         for idx, item in enumerate(data_normalized):
    #             item["backend"] = self.display_name
    #             item["backend_name"] = self.name
    #             item["geoaddress_id"] = self._generate_geoaddress_id(item.get('latitude'), item.get('longitude'))
    #             item["text"] = self._build_address_string(item)
    #             for field_name, format_config in GEOADDRESS_FIELDS_FORMATS.items():
    #                 item[field_name] = self.insert_text_formatted(item, cast("list[Any]", format_config), field_name)
#
    #             feature = raw_list[idx] if raw_list and idx < len(raw_list) else None
    #             if not item.get('confidence'):
    #                 item['confidence'] = self._calculate_confidence(item, feature=feature, importance_key=self.importance_key)
    #             if not item.get('relevance'):
    #                 query_components = self._extract_query_components(raw_result, service_name)
    #                 query_lat = query_components.get('latitude')
    #                 query_lon = query_components.get('longitude')
    #                 item['relevance'] = self._calculate_relevance(query_components or {}, item, query_latitude=query_lat, query_longitude=query_lon)
#
    #     elif isinstance(data_normalized, dict):
    #         data_normalized["backend"] = self.display_name
    #         data_normalized["backend_name"] = self.name
    #         data_normalized["geoaddress_id"] = self._generate_geoaddress_id(data_normalized.get('latitude'), data_normalized.get('longitude'))
    #         data_normalized["text"] = self._build_address_string(data_normalized)
    #         for field_name, format_config in GEOADDRESS_FIELDS_FORMATS.items():
    #             data_normalized[field_name] = self.insert_text_formatted(data_normalized, cast("list[Any]", format_config), field_name)
#
    #         feature = raw_result if isinstance(raw_result, dict) else (raw_result[0] if isinstance(raw_result, list) and raw_result else None)
    #         if not data_normalized.get('confidence'):
    #             data_normalized['confidence'] = self._calculate_confidence(data_normalized, feature=feature, importance_key=self.importance_key)
    #         if not data_normalized.get('relevance'):
    #             query_components = self._extract_query_components(raw_result, service_name)
    #             query_lat = query_components.get('latitude')
    #             query_lon = query_components.get('longitude')
    #             data_normalized['relevance'] = self._calculate_relevance(query_components or {}, data_normalized, query_latitude=query_lat, query_longitude=query_lon)
    #     return data_normalized

    def _extract_query_components(self, raw_result: Any, service_name: str | None) -> dict[str, Any]:
        query_components: dict[str, Any] = {}
        if service_name == "addresses_autocomplete":
            query = getattr(self, 'addresses_autocomplete_query', None)
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

    def insert_text_formatted(self, data: Any, normalized: dict[str, Any], format_config: list[Any]) -> list[str] | list[list[str]]:
        result: list[Any] = []
        config = self.services_cfg.get("addresses_autocomplete", {})
        for item in format_config:
            if isinstance(item, list):
                group_parts = self.insert_text_formatted(data, normalized, item)
                if group_parts:
                    result.append(group_parts)
            else:
                field_cfg = config.get('fields', {}).get(item, {})
                if item in normalized:
                    value = normalized[item]
                elif hasattr(self, f'get_normalize_{item}') and callable(getattr(self, f'get_normalize_{item}')):
                    value = getattr(self, f'get_normalize_{item}')(data)
                else:
                    value = self._normalize_recursive(data, item, field_cfg.get('source'))
                if value:
                    result.append(str(value))
        return result if result else []

    @staticmethod
    def _round_score(score: float, decimals: int = 2) -> float:
        return round(float(score), decimals)

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

    def get_insert_normalized_relevance(self, data: Any, normalized: dict[str, Any], _config: dict[str, Any]) -> float | None:
        service_name = getattr(self, 'current_service_name', None)
        raw_result = None
        if hasattr(self, '_service_results_cache') and service_name:
            raw_result = self._service_results_cache.get(service_name, {}).get('result')

        query_components = self._extract_query_components(raw_result, service_name)
        query_lat = query_components.get('latitude')
        query_lon = query_components.get('longitude')

        cfg = self.services_cfg.get(service_name or "addresses_autocomplete", {})
        result_latitude = self._normalize_recursive(data, 'latitude', cfg.get('fields', {}).get('latitude', {}).get('source'))
        result_longitude = self._normalize_recursive(data, 'longitude', cfg.get('fields', {}).get('longitude', {}).get('source'))

        normalized_result = {
            'address_line1': normalized.get('address_line1', ''),
            'postal_code': normalized.get('postal_code', ''),
            'city': normalized.get('city', ''),
            'latitude': result_latitude,
            'longitude': result_longitude,
        }

        return self._calculate_relevance(query_components or {}, normalized_result, query_latitude=query_lat, query_longitude=query_lon)

    def get_insert_normalized_confidence(self, data: Any, _normalized: dict[str, Any], _config: dict[str, Any]) -> float | None:
        service_name = getattr(self, 'current_service_name', None)
        cfg = self.services_cfg.get(service_name or "addresses_autocomplete", {})
        return self._calculate_confidence(data=data, config=cfg, feature=data, importance_key=self.importance_key)

    def get_insert_normalized_backend(self, _data: Any, _normalized: dict[str, Any], _config: dict[str, Any]) -> str:
        return self.name

    def get_insert_normalized_backend_name(self, _data: Any, _normalized: dict[str, Any], _config: dict[str, Any]) -> str:
        return self.display_name

    def get_insert_normalized_text_aligned(self, _data: Any, normalized: dict[str, Any], _config: dict[str, Any]) -> list[str] | list[list[str]]:
        format_config = cast(list[Any], GEOADDRESS_FIELDS_FORMATS["text_aligned"])
        return self.insert_text_formatted(_data, normalized, format_config)

    def get_insert_normalized_text_2lines(self, _data: Any, normalized: dict[str, Any], _config: dict[str, Any]) -> list[str] | list[list[str]]:
        format_config = cast(list[Any], GEOADDRESS_FIELDS_FORMATS["text_2lines"])
        return self.insert_text_formatted(_data, normalized, format_config)

    def get_insert_normalized_text_3lines(self, _data: Any, normalized: dict[str, Any], _config: dict[str, Any]) -> list[str] | list[list[str]]:
        format_config = cast(list[Any], GEOADDRESS_FIELDS_FORMATS["text_3lines"])
        return self.insert_text_formatted(_data, normalized, format_config)

    def get_insert_normalized_text_full(self, _data: Any, normalized: dict[str, Any], _config: dict[str, Any]) -> list[str] | list[list[str]]:
        format_config = cast(list[Any], GEOADDRESS_FIELDS_FORMATS["text_full"])
        return self.insert_text_formatted(_data, normalized, format_config)

    def get_insert_normalized_geoaddress_id(self, data: Any, _normalized: dict[str, Any], _config: dict[str, Any]) -> str:
        cfg = self.services_cfg.get("addresses_autocomplete", {})
        latitude = self._normalize_recursive(data, 'latitude', cfg['fields'].get('latitude').get('source'))
        longitude = self._normalize_recursive(data, 'longitude', cfg['fields'].get('longitude').get('source'))
        return self._generate_geoaddress_id(latitude, longitude)

    def _generate_geoaddress_id(self, latitude: float | None, longitude: float | None) -> str:
        if latitude is None or longitude is None:
            return f"{self.name}-unknown"
        return f"{self.name}_{latitude}:{longitude}"
