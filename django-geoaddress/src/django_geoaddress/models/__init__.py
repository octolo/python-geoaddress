"""Models for django_geoaddress."""

from .provider import GeoaddressProviderModel
from .service import GeoaddressServiceModel
from .suggest import AddressModel, BaseAddressModel

__all__ = [
    "AddressModel",
    "BaseAddressModel",
    "GeoaddressProviderModel",
    "GeoaddressServiceModel",
]
