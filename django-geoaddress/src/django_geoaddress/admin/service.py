from django_providerkit.admin.service import ProviderServiceAdmin
from django_geoaddress.models.service import GeoaddressServiceModel
from django.contrib import admin

@admin.register(GeoaddressServiceModel)
class GeoaddressServiceAdmin(ProviderServiceAdmin):
    """Admin for geoaddress services."""
    pass