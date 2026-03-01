"""Provider model for geoaddress providers."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from virtualqueryset.models import VirtualModel
from geoaddress.providers.base import GeoaddressProvider
from django_providerkit.models.define import define_provider_fields, define_service_fields
from django_providerkit.managers import BaseProviderManager

services = list(GeoaddressProvider.services_cfg.keys())


@define_provider_fields(primary_key='name')
@define_service_fields(services)
class GeoaddressProviderModel(VirtualModel):
    """Virtual model for geoaddress providers."""

    name: models.CharField = models.CharField(
        max_length=255,
        verbose_name=_("Name"),
        help_text=_("Provider name (e.g., nominatim)"),
        primary_key=True,
    )

    objects = BaseProviderManager(package_name='geoaddress')

    class Meta:
        managed = False
        app_label = 'django_geoaddress'
        verbose_name = _("Provider")
        verbose_name_plural = _("Providers")
        ordering = ['-priority', 'name']

    def __str__(self) -> str:
        return self.display_name or self.name
