from __future__ import annotations

import json
from typing import Any

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.forms.widgets import TextInput
from django.template.loader import render_to_string
from django.urls import NoReverseMatch, reverse
from geoaddress import (
    DEFAULT_DISPLAY,
    GEOADDRESS_FIELDS_ESSENTIALS,
    GEOADDRESS_FIELDS_OPTIONALS,
    GEOADDRESS_FIELDS_COORDINATES,
    GEOADDRESS_FULL_FIELDS,
    format_address_lines,
)
from geoaddress.formatting import DisplaySpec


class GeoaddressValue(dict):
    """Simple wrapper to format address as string."""

    def __init__(self, data: dict[str, Any] | None = None):
        """Initialize with address data."""
        super().__init__(data or {})

    def __str__(self) -> str:
        """Format address using GEOADDRESS_FIELDS_ESSENTIALS order."""
        parts = [str(self.get(k)) for k in GEOADDRESS_FIELDS_ESSENTIALS.keys() if self.get(k)]
        return ", ".join(parts)


class GeoaddressAutocompleteWidget(TextInput):
    template_name = "django_geoaddress/autocomplete.html"
    address_url_name = "django_geoaddress:redirect_to_address_list"
    redirect_url = "django_geoaddress:redirect_to_address"

    class Media:
        css = {"all": ("css/geoaddress_autocomplete.css",)}
        js = ("js/geoaddress_autocomplete.js",)

    def __init__(
        self,
        attrs=None,
        display: DisplaySpec = DEFAULT_DISPLAY,
        model: type[models.Model] | None = None,
        field_name: str = "",
    ):
        self.display = display
        self.model = model
        self.field_name = field_name
        super().__init__(attrs)

    def get_url(self) -> str:
        """Return the autocomplete URL."""
        return reverse(self.address_url_name)

    def get_inspect_urls(self) -> tuple[str, str]:
        try:
            return (
                reverse("admin:django_geoaddress_addressmodel_inspect_address_result"),
                reverse("admin:django_geoaddress_addressmodel_inspect_address"),
            )
        except NoReverseMatch:
            return "", ""

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context["autocomplete_url"] = self.get_url()
        inspect_url, inspect_form_url = self.get_inspect_urls()
        context["inspect_url"] = inspect_url
        context["inspect_form_url"] = inspect_form_url
        context["redirect_url"] = inspect_url or inspect_form_url
        context["field_name"] = self.field_name or name.split("-")[-1]
        try:
            context["content_type_id"] = (
                ContentType.objects.get_for_model(self.model).pk if self.model else ""
            )
        except (LookupError, ValueError, RuntimeError):
            context["content_type_id"] = ""
        widget_attrs = context["widget"].get("attrs") or {}
        context["is_readonly"] = self._is_locked(widget_attrs) or self._is_locked(attrs)
        if isinstance(value, dict):
            values = value
        elif value:
            try:
                values = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                values = {}
        else:
            values = {}

        context["value"] = values
        context["readonly_lines"] = format_address_lines(values, self.display) if isinstance(values, dict) else []
        geoaddress_data = {
            k: {
                "value": values.get(k) or "" if isinstance(values, dict) else "",
                "label": _(v.get("label", k)),
            }
            for k, v in GEOADDRESS_FIELDS_ESSENTIALS.items()
        }
        geoaddress_optionals = {
            k: {
                "value": values.get(k) or "" if isinstance(values, dict) else "",
                "label": _(v.get("label", k)),
            }
            for k, v in GEOADDRESS_FIELDS_OPTIONALS.items()
        }
        geoaddress_coordinates = {
            k: {
                "value": values.get(k) or "" if isinstance(values, dict) else "",
                "label": _(v.get("label", k)),
            }
            for k, v in GEOADDRESS_FIELDS_COORDINATES.items()
        }
        text_full = [data["value"] for data in geoaddress_data.values() if data["value"]]
        context.update({
            "search_value": ", ".join(text_full) if text_full else "",
            "geoaddress_data": geoaddress_data,
            "geoaddress_optionals": geoaddress_optionals,
            "geoaddress_coordinates": geoaddress_coordinates,
            "geoaddress_fields": list(GEOADDRESS_FULL_FIELDS.keys()),
        })
        return context

    @staticmethod
    def _is_locked(attrs: dict | None) -> bool:
        if not attrs:
            return False
        for key in ("disabled", "readonly"):
            if key in attrs and attrs[key] not in (False, None):
                return True
        return False

class GeoaddressField(models.JSONField):
    """Field to store geoaddress data via AddressModel with autocomplete."""

    def __init__(self, *args: Any, display: DisplaySpec = DEFAULT_DISPLAY, **kwargs: Any):
        if isinstance(display, str):
            from geoaddress.formatting import resolve_display

            resolve_display(display)
        self.display = display
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.display != DEFAULT_DISPLAY:
            kwargs["display"] = self.display
        return name, path, args, kwargs

    def from_db_value(self, value: Any, _expression: Any, _connection: Any) -> GeoaddressValue | None:
        """Convert database value to GeoaddressValue."""
        if value is None:
            return None
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                value = {}
        return GeoaddressValue(value) if isinstance(value, dict) else None

    def to_python(self, value: Any) -> GeoaddressValue | None:
        """Convert value to GeoaddressValue."""
        if value is None:
            return None
        if isinstance(value, GeoaddressValue):
            return value
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except (json.JSONDecodeError, TypeError):
                value = {}
        return GeoaddressValue(value) if isinstance(value, dict) else None

    def get_prep_value(self, value: Any) -> dict | None:
        """Prepare value for database storage."""
        if value is None:
            return None
        if isinstance(value, GeoaddressValue):
            return dict(value)
        if isinstance(value, dict):
            return value
        return None

    def formfield(self, **kwargs: Any) -> Any:
        """Ensure the custom widget is used.

        Args:
            **kwargs: Additional arguments for formfield

        Returns:
            Form field with custom widget
        """
        model = getattr(self, "model", None)
        field_name = getattr(self, "name", "") or ""
        widget = kwargs.get("widget")
        if widget is None:
            kwargs["widget"] = GeoaddressAutocompleteWidget(
                display=self.display,
                model=model,
                field_name=field_name,
            )
        elif isinstance(widget, type) and issubclass(widget, GeoaddressAutocompleteWidget):
            kwargs["widget"] = widget(
                display=self.display,
                model=model,
                field_name=field_name,
            )
        elif isinstance(widget, GeoaddressAutocompleteWidget):
            widget.display = self.display
            widget.model = model
            widget.field_name = field_name
        return super().formfield(**kwargs)