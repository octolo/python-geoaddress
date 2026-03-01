"""URL configuration for testing django-geoaddress."""

import django
import geoaddress
import django_geoaddress
from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter

from tests.app.viewsets import LocationViewSet

router = DefaultRouter()
router.register(r"api/locations", LocationViewSet, basename="location")

urlpatterns = [
    path("", RedirectView.as_view(url="/locations/", permanent=False)),
    path("admin/", admin.site.urls),
    path("django_geoaddress/", include("django_geoaddress.urls")),
    path("locations/", include("tests.app.urls")),
    path("", include(router.urls)),
]

_version = f"(Django {django.get_version()}, geoaddress {geoaddress.__version__}/{django_geoaddress.__version__})"
admin.site.site_header = f"Django GeoAddress - Administration {_version}"
admin.site.site_title = f"Django GeoAddress Admin {_version}"
admin.site.index_title = f"Welcome to Django GeoAddress {_version}"
