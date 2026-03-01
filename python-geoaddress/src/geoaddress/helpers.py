from typing import Any, cast

from providerkit.helpers import call_providers, get_providers

from .providers.base import GeoaddressProvider


def get_address_providers(*args: Any, **kwargs: Any) -> dict[str, Any] | str:
    """Get address providers."""
    lib_name = kwargs.pop('lib_name', 'geoaddress')
    return cast('dict[str, Any] | str', get_providers(*args, lib_name=lib_name, **kwargs))


def get_address_provider(attribute_search: dict[str, Any], *args: Any, **kwargs: Any) -> GeoaddressProvider:
    """Get address provider by attribute search."""
    lib_name = kwargs.pop('lib_name', 'geoaddress')
    providers = get_providers(*args, attribute_search=attribute_search, format="python", lib_name=lib_name, **kwargs)
    if not providers:
        raise ValueError("No providers found")
    if len(providers) > 1:
        raise ValueError(f"Expected 1 provider, got {len(providers)}")
    return cast('GeoaddressProvider', providers[0])

def search_addresses(query: str, *args: Any, **kwargs: Any) -> Any:
    """Search addresses using providers."""
    return call_providers(
        *args,
        command="search_addresses",
        lib_name="geoaddress",
        query=query,
        **kwargs,
    )

def addresses_autocomplete(query: str, *args: Any, **kwargs: Any) -> Any:
    """Search addresses using providers."""
    return call_providers(
        *args,
        command="addresses_autocomplete",
        lib_name="geoaddress",
        query=query,
        **kwargs,
    )

def reverse_geocode(latitude: float, longitude: float, *args: Any, **kwargs: Any) -> Any:
    """Reverse geocode coordinates to address using providers."""
    return call_providers(
        *args,
        command="reverse_geocode",
        latitude=latitude,
        lib_name="geoaddress",
        longitude=longitude,
        **kwargs,
    )
