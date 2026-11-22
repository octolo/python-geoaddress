"""Admin for tests.app."""

from django.contrib import admin
from geoaddress import format_address_lines

from django_geoaddress.fields import GeoaddressAutocompleteWidget

from .forms import LocationReadonlyForm
from .models import Addressbook, Location, LocationReadonly


class LocationAddressPreviewMixin:
    """Display the address widget as read-only in a changelist."""

    @property
    def media(self):
        """Include the widget assets in the changelist."""
        return super().media + GeoaddressAutocompleteWidget().media

    @admin.display(description='Address')
    def address_display(self, obj):
        """Render the stored address with its configured display layout."""
        field = obj._meta.get_field('address')
        widget = GeoaddressAutocompleteWidget(
            attrs={'readonly': True, 'data_object_id': str(obj.pk)},
            display=field.display,
            model=type(obj),
            field_name='address',
        )
        address = obj.address
        if (
            address
            and address.get('text')
            and not format_address_lines(address, field.display)
        ):
            address = {**address, 'address_line1': address['text']}
        return widget.render(f'address-preview-{obj.pk}', address)


@admin.register(Location)
class LocationAdmin(LocationAddressPreviewMixin, admin.ModelAdmin):
    """Admin for Location model."""
    list_display = ["name", "address_display", "created_at", "updated_at"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["name"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        (None, {
            "fields": ["name", "address"],
        }),
        ("Timestamps", {
            "fields": ["created_at", "updated_at"],
        }),
    ]

class LocationInline(admin.TabularInline):
    """Inline for Location model."""
    model = Location
    extra = 0
    fields = ["name", "address", "created_at", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]


class LocationReadonlyInline(admin.TabularInline):
    """Inline for LocationReadonly: address is locked after it is first saved."""

    model = LocationReadonly
    form = LocationReadonlyForm
    extra = 0
    fields = ["name", "address", "created_at", "updated_at"]
    readonly_fields = ["created_at", "updated_at"]


@admin.register(LocationReadonly)
class LocationReadonlyAdmin(LocationAddressPreviewMixin, admin.ModelAdmin):
    """Admin for LocationReadonly: address is locked after it is first saved."""

    form = LocationReadonlyForm
    list_display = ["name", "address_display", "created_at", "updated_at"]
    list_filter = ["created_at", "updated_at"]
    search_fields = ["name"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = [
        (None, {
            "fields": ["name", "address"],
        }),
        ("Timestamps", {
            "fields": ["created_at", "updated_at"],
        }),
    ]

@admin.register(Addressbook)
class AddressbookAdmin(admin.ModelAdmin):
    """Admin for Addressbook model."""
    list_display = ["name"]
    search_fields = ["name"]
    inlines = [LocationInline, LocationReadonlyInline]