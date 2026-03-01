"""Django app configuration."""

from django.apps import AppConfig


class DjangoGeoaddressConfig(AppConfig):
    """Configuration for the django_geoaddress app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "django_geoaddress"
    verbose_name = "GeoAddress"
