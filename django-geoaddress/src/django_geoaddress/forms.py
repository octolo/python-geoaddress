"""Forms for django-geoaddress admin views."""

from __future__ import annotations

from django import forms
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import FieldDoesNotExist
from django.utils.translation import gettext_lazy as _

from django_geoaddress.fields import GeoaddressField


def geoaddress_content_types():
    """Content types whose model has at least one GeoaddressField."""
    pks: list[int] = []
    for content_type in ContentType.objects.all():
        model = content_type.model_class()
        if model is None:
            continue
        if any(isinstance(field, GeoaddressField) for field in model._meta.fields):
            pks.append(content_type.pk)
    return ContentType.objects.filter(pk__in=pks).order_by("app_label", "model")


class InspectAddressForm(forms.Form):
    """Locate a stored GeoaddressField on any model instance."""

    content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.none(),
        label=_("Content type"),
    )
    object_id = forms.CharField(
        label=_("ID"),
    )
    field = forms.CharField(
        label=_("Field"),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["content_type"].queryset = geoaddress_content_types()

    def clean(self):
        cleaned = super().clean()
        content_type = cleaned.get("content_type")
        object_id = cleaned.get("object_id")
        field_name = cleaned.get("field")
        if not (content_type and object_id and field_name):
            return cleaned

        model = content_type.model_class()
        if model is None:
            raise forms.ValidationError(_("This content type has no model."))

        try:
            model_field = model._meta.get_field(field_name)
        except FieldDoesNotExist as exc:
            raise forms.ValidationError(
                {"field": _("Unknown field '%(field)s' on %(model)s.") % {
                    "field": field_name,
                    "model": model._meta.label,
                }}
            ) from exc

        if not isinstance(model_field, GeoaddressField):
            raise forms.ValidationError(
                {"field": _("'%(field)s' is not a GeoaddressField.") % {"field": field_name}}
            )

        try:
            instance = model._default_manager.get(pk=object_id)
        except (model.DoesNotExist, ValueError, TypeError) as exc:
            raise forms.ValidationError(
                {"object_id": _("No %(model)s with id '%(object_id)s'.") % {
                    "model": model._meta.verbose_name,
                    "object_id": object_id,
                }}
            ) from exc

        cleaned["instance"] = instance
        cleaned["model_field"] = model_field
        return cleaned
