"""Managers for django_geoaddress."""

from .suggest import AddressManager

__all__ = ["AddressManager", "ProviderManager"]
