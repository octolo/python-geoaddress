from pathlib import Path
from typing import Any

from providerkit.helpers import get_providerkit, get_providers, call_providers
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
    additional_args = kwargs.get("additional_args", {})
    results = call_providers(command="search_addresses", query=query, lib_name="geoaddress", **additional_args)
    print(results)
    return "test"

    #results = pvk.get_service_result("search_addresses")
    #if not results:
    #    return None
#
    #if first and results:
    #    provider_result = results[0]
    #    if "error" in provider_result:
    #        raise RuntimeError(provider_result["error"])
    #    provider = provider_result["provider"]
    #    return provider.call_service("search_addresses", query=query, **additional_args)
#
    #all_results = []
    #for provider_result in results:
    #    if "error" in provider_result:
    #        continue
    #    provider = provider_result["provider"]
    #    result = provider.call_service("search_addresses", query=query, **additional_args)
    #    all_results.append(result)
    #return all_results


def get_address_by_reference(  # noqa: ARG001
    reference: str,
    first: bool = False,
    providers: dict[str, Any] | None = None,
    json: str | Path | None = None,
    lib_name: str = "geoaddress",
    config: list[dict[str, Any]] | None = None,
    dir_path: str | Path | None = None,
    base_module: str | None = None,
    query_string: str | None = None,
    search_fields: list[str] | None = None,
    **kwargs: Any,
) -> Any:
    """Get address by reference using providers."""
    additional_args = kwargs.get("additional_args", {})
    additional_args["reference"] = reference

    providers_args = {
        "json": json,
        "lib_name": lib_name,
        "config": config,
        "dir_path": dir_path,
        "base_module": base_module,
        "query_string": query_string,
        "search_fields": search_fields,
    }
    providers_args.update({k: v for k, v in kwargs.items() if k != "additional_args"})

    pvk = get_providerkit(**providers_args)
    pvk.execute_providers("get_address_by_reference", first=first, lib_name=lib_name, **providers_args, **additional_args)

    results = pvk.get_service_result("get_address_by_reference")
    if not results:
        return None

    if first and results:
        provider_result = results[0]
        if "error" in provider_result:
            raise RuntimeError(provider_result["error"])
        provider = provider_result["provider"]
        return provider.call_service("get_address_by_reference", reference=reference, **additional_args)

    all_results = []
    for provider_result in results:
        if "error" in provider_result:
            continue
        provider = provider_result["provider"]
        result = provider.call_service("get_address_by_reference", reference=reference, **additional_args)
        all_results.append(result)
    return all_results
