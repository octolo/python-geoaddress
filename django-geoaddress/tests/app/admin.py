"""Admin for tests.app."""

from django.contrib import admin

from .forms import LocationReadonlyForm
from .models import Addressbook, Location, LocationReadonly



@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
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

    def address_display(self, obj):
        """Display address text."""
        if obj.address and obj.address.get("text"):
            return obj.address["text"]
        return "-"
    
    address_display.short_description = "Address"

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
class LocationReadonlyAdmin(admin.ModelAdmin):
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

    def address_display(self, obj):
        """Display address text."""
        if obj.address and obj.address.get("text"):
            return obj.address["text"]
        return "-"

    address_display.short_description = "Address"


@admin.register(Addressbook)
class AddressbookAdmin(admin.ModelAdmin):
    """Admin for Addressbook model."""
    list_display = ["name"]
    search_fields = ["name"]
    inlines = [LocationInline, LocationReadonlyInline]