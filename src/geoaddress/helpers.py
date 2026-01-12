from typing import Any

from providerkit.helpers import get_providers, call_providers
from .providers import GeoaddressProvider

def get_address_providers(*args: Any, **kwargs: Any) -> dict[str, Any] | str:
    """Get address providers."""
    lib_name = kwargs.pop('lib_name', 'geoaddress')
    return get_providers(lib_name=lib_name, *args, **kwargs)


def get_address_provider(attribute_search: dict[str, Any], *args: Any, **kwargs: Any) -> GeoaddressProvider:
    """Get address provider by attribute search."""
    lib_name = kwargs.pop('lib_name', 'geoaddress')
    providers = get_providers(lib_name=lib_name, attribute_search=attribute_search, format="python", *args, **kwargs)
    if not providers:
        raise ValueError("No providers found")
    if len(providers) > 1:
        raise ValueError(f"Expected 1 provider, got {len(providers)}")
    return providers[0]  # type: ignore[no-any-return]


def search_addresses(query: str, *args: Any, **kwargs: Any) -> Any:
    """Search addresses using providers."""
    return call_providers(
        command="search_addresses",
        query=query,
        lib_name="geoaddress",
        *args,
        **kwargs,
    )

def reverse_geocode(latitude: float, longitude: float, *args: Any, **kwargs: Any) -> Any:
    """Reverse geocode coordinates to address using providers."""
    return call_providers(
        command="reverse_geocode",
        latitude=latitude,
        longitude=longitude,
        lib_name="geoaddress",
        *args,
        **kwargs,
    )
