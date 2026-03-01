from django.db import models
from django.utils.translation import gettext_lazy as _

from django_providerkit.managers.service import ProviderServiceManager
from django_providerkit.models.service import ProviderServiceModelBase


class GeoaddressServiceModel(ProviderServiceModelBase):
    """Virtual model for geoaddress services."""

    objects = ProviderServiceManager(package_name='geoaddress')

    class Meta:
        app_label = 'django_geoaddress'
        managed = False
        verbose_name = _('Provider Service')
        verbose_name_plural = _('Provider Services')