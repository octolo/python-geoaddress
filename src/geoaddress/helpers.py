from pathlib import Path
from typing import Any

from providerkit.helpers import get_providers, try_providers, try_providers_first


def get_address_providers(
    *,
    json: str | Path | None = None,
    lib_name: str = "geoaddress",
    config: list[dict[str, Any]] | None = None,
    dir_path: str | Path | None = None,
    base_module: str | None = None,
    query_string: str | None = None,
    search_fields: list[str] | None = None,
    attribute_search: dict[str, str] | None = None,
    format: str | None = None,
) -> dict[str, Any] | str:
    """Get address providers."""
    providers = get_providers(  # type: ignore[no-any-return]
        json=json,
        lib_name=lib_name,
        config=config,
        dir_path=dir_path,
        base_module=base_module,
        query_string=query_string,
        search_fields=search_fields,
        attribute_search=attribute_search,
        format=format,
    )
    if not len(providers):
        raise ValueError("No providers found")
    return providers  # type: ignore[no-any-return]


def get_address_provider(
    name: str,
) -> Any:
    """Get address provider."""
    providers = get_providers(  # type: ignore[no-any-return]
        lib_name="geoaddress",
        attribute_search={"name": name},
        format="python",
    )
    if len(providers) > 1:
        raise ValueError(f"Expected 1 provider, got {len(providers)}")
    return providers[0]


def search_addresses(
    query: str,
    first: bool = False,
    providers: dict[str, Any] | None = None,
    json: str | Path | None = None,
    lib_name: str = "geoaddress",
    config: list[dict[str, Any]] | None = None,
    dir_path: str | Path | None = None,
    base_module: str | None = None,
    query_string: str | None = None,
    search_fields: list[str] | None = None,
    parallel: bool = False,
    **kwargs: Any,
) -> Any:
    """Search addresses using providers."""
    if "additional_args" not in kwargs:
        kwargs["additional_args"] = {}
    kwargs["additional_args"]["query"] = query

    providers_args = {
        "command": "search_addresses",
        "json": json,
        "lib_name": lib_name,
        "config": config,
        "dir_path": dir_path,
        "base_module": base_module,
        "query_string": query_string,
        "search_fields": search_fields,
    }
    providers_args.update(kwargs)

    if first:
        return try_providers_first(**providers_args)
    return try_providers(**providers_args)


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
    if "additional_args" not in kwargs:
        kwargs["additional_args"] = {}
    kwargs["additional_args"]["reference"] = reference
    providers_args = {
        "command": "get_address_by_reference",
        "json": json,
        "lib_name": lib_name,
        "config": config,
        "dir_path": dir_path,
        "base_module": base_module,
        "query_string": query_string,
        "search_fields": search_fields,
    }
    providers_args.update(kwargs)

    if first:
        return try_providers_first(**providers_args)
    return try_providers(**providers_args)
