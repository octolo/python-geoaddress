"""Admin for address suggestion model."""

from __future__ import annotations

from typing import Any

from django.contrib import admin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
import json

from django_boosted import AdminBoostModel, admin_boost_view

from ..forms import InspectAddressForm
from ..models.suggest import AddressModel
from ..models.provider import GeoaddressProviderModel
from geoaddress import (
    GEOADDRESS_FIELDS_DESCRIPTIONS,
    GEOADDRESS_FIELDS_ESSENTIALS,
    GEOADDRESS_FIELDS_OPTIONALS,
    GEOADDRESS_FIELDS_COORDINATES,
)

from django_providerkit.admin.filters import FirstServiceAdminFilter, BackendServiceAdminFilter

BackendServiceAdminFilter.provider_model = GeoaddressProviderModel

@admin.register(AddressModel)
class AddressAdmin(AdminBoostModel):
    boost_views = [
        "inspect_address",
        "inspect_address_result",
        "address_autocomplete_view",
    ]
    list_filter = [FirstServiceAdminFilter, BackendServiceAdminFilter]
    list_display = ["text_full", "backend_name_display"]
    search_fields = ["address_line1", "backend"]
    readonly_fields = [
        "address_line1",
        "backend",
    ]

    def change_fieldsets(self):
        self.add_to_fieldset(None, GEOADDRESS_FIELDS_ESSENTIALS.keys())
        self.add_to_fieldset(_("Optionals"), GEOADDRESS_FIELDS_OPTIONALS.keys())
        self.add_to_fieldset(_("Coordinates"), GEOADDRESS_FIELDS_COORDINATES.keys())
        self.add_to_fieldset(_("Backend"), ["backend_name_display", "geoaddress_id", "raw_result"])

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def backend_name_display(self, obj: AddressModel | None) -> str:
        if not obj or not obj.backend or not obj.backend_name:
            return "-"
        url = reverse("admin:django_geoaddress_geoaddressprovidermodel_change", args=[obj.backend])
        return format_html('<a href="{}">{}</a>', url, obj.backend_name)
    backend_name_display.short_description = _("Backend name")

    def raw_result(self, obj: AddressModel | None) -> str:
        raw = self.model.objects.get_raw_result(command="reverse_geocode")
        raw = json.dumps(raw[0].get("result"), indent=4, ensure_ascii=False)
        return mark_safe(f"<pre>{raw}</pre>")
    raw_result.short_description = _("Raw result")

    def get_object(self, request: HttpRequest, object_id: str, _from_field: str | None = None) -> AddressModel | None:
        qs = self.model.objects.reverse_geocode(geoaddress_id=object_id)
        return qs.first()

    def get_queryset(self, request: HttpRequest) -> Any:
        query = request.GET.get("q")
        if query:
            kwargs = {"first": bool(request.GET.get("first"))}
            if request.GET.get("bck"):
                kwargs["attribute_search"] = {"name": request.GET.get("bck")}
            return self.model.objects.search_addresses(query=query, **kwargs)
        return self.model.objects.none()

    def get_search_results(self, request: HttpRequest, queryset: Any, search_term: str) -> tuple[Any, bool]:
        if search_term:
            return queryset, False
        return queryset, False

    @admin_boost_view("form", _("Inspect address"), requires_object=False)
    def inspect_address(self, request: HttpRequest) -> dict[str, Any] | HttpResponse:
        if request.method == "POST":
            form = InspectAddressForm(request.POST)
            if form.is_valid():
                return redirect(self._inspect_result_url(form.cleaned_data))
        else:
            form = InspectAddressForm(initial=request.GET)
        return {
            "form": form,
            "buttons": {"_inspect": _("Inspect")},
        }

    @admin_boost_view(
        "form",
        _("Inspect address"),
        requires_object=False,
        hidden=True,
        template_name="django_geoaddress/inspect_address.html",
        path_fragment="inspect-address-result",
    )
    def inspect_address_result(self, request: HttpRequest) -> dict[str, Any] | HttpResponse:
        form = InspectAddressForm(request.GET)
        if not form.is_valid():
            url = reverse(
                "admin:django_geoaddress_addressmodel_inspect_address",
                current_app=self.admin_site.name,
            )
            if request.GET:
                url = f"{url}?{request.GET.urlencode()}"
            return redirect(url)

        cleaned = form.cleaned_data
        instance = cleaned["instance"]
        stored = getattr(instance, cleaned["field"])
        stored_payload = dict(stored) if stored else {}
        geoaddress_id = stored_payload.get("geoaddress_id") if stored_payload else None
        api_response = None
        api_error = None
        if geoaddress_id:
            try:
                AddressModel.objects.reverse_geocode(geoaddress_id=geoaddress_id)
                raw = AddressModel.objects.get_raw_result(command="reverse_geocode")
                api_response = self._pretty_json(self._extract_api_payload(raw))
            except Exception as exc:
                api_error = str(exc)

        return {
            "stored_json": self._pretty_json(stored_payload),
            "api_response": api_response,
            "api_error": api_error,
            "geoaddress_id": geoaddress_id,
            "content_type": cleaned["content_type"],
            "object_id": cleaned["object_id"],
            "field_name": cleaned["field"],
            "instance_label": str(instance),
            "inspect_form_url": f"{reverse('admin:django_geoaddress_addressmodel_inspect_address', current_app=self.admin_site.name)}?{urlencode({'content_type': cleaned['content_type'].pk, 'object_id': cleaned['object_id'], 'field': cleaned['field']})}",
        }

    def _inspect_result_url(self, cleaned: dict[str, Any]) -> str:
        url = reverse(
            "admin:django_geoaddress_addressmodel_inspect_address_result",
            current_app=self.admin_site.name,
        )
        query = urlencode({
            "content_type": cleaned["content_type"].pk,
            "object_id": cleaned["object_id"],
            "field": cleaned["field"],
        })
        return f"{url}?{query}"

    @staticmethod
    def _pretty_json(value: Any) -> str:
        return json.dumps(value, indent=2, ensure_ascii=False, default=str)

    @staticmethod
    def _extract_api_payload(raw: Any) -> Any:
        if isinstance(raw, list):
            payload = []
            for item in raw:
                if not isinstance(item, dict):
                    payload.append(item)
                    continue
                if "result" in item:
                    payload.append(item["result"])
                elif "error" in item:
                    payload.append({"error": item["error"]})
                else:
                    payload.append({k: v for k, v in item.items() if k != "provider"})
            return payload
        return raw

    @admin_boost_view("json", "Autocomplete View")
    def address_autocomplete_view(self, request: HttpRequest) -> dict[str, Any]:
        search_term = request.GET.get("term") or request.GET.get("q")
        qs = self.model.objects.none()
        if search_term:
            kwargs = {
                "first": True,
            }
            qs = self.model.objects.addresses_autocomplete(query=search_term, **kwargs)
        return {
            "addresses": [
                {field: getattr(obj, field) for field in GEOADDRESS_FIELDS_DESCRIPTIONS}
                for obj in qs
            ],
            "pagination": {
                "more": False,
            },
        }
