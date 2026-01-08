"""Reverse geocode command for getting address from coordinates."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from qualitybase.cli import _get_package_name  # noqa: TID252
from qualitybase.commands import parse_attr_args, parse_single_arg, parse_value_arg
from qualitybase.commands.base import Command
from providerkit.helpers import get_providerkit

if TYPE_CHECKING:
    from pathlib import Path


def _parse_all_args(
    args: list[str],
) -> tuple[str, float | None, float | None, str | None, str | None, str | None, dict[str, str], bool, bool, bool]:
    """Parse all command line arguments."""
    output_format = "table"
    latitude: float | None = None
    longitude: float | None = None
    dir_path: str | Path | None = None
    json_path: str | Path | None = None
    query_string: str | None = None
    attribute_search: dict[str, str] = {}
    first: bool = False
    raw: bool = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--lat":
            i, value = parse_value_arg(args, i, arg)
            if value:
                try:
                    latitude = float(value)
                except ValueError:
                    print(f"Error: Invalid latitude value: {value}", file=sys.stderr)
                    return "", None, None, None, None, None, {}, False, False, True
        elif arg == "--lon":
            i, value = parse_value_arg(args, i, arg)
            if value:
                try:
                    longitude = float(value)
                except ValueError:
                    print(f"Error: Invalid longitude value: {value}", file=sys.stderr)
                    return "", None, None, None, None, None, {}, False, False, True
        elif arg == "--attr":
            result = parse_attr_args(args, i, attribute_search)
            if result is None:
                return "", None, None, None, None, None, {}, False, False, True
            i = result
        elif arg == "--format":
            i, value = parse_value_arg(args, i, arg)
            if value:
                output_format = value
        elif arg == "--dir":
            i, value = parse_value_arg(args, i, arg)
            if value:
                dir_path = value
        elif arg == "--json":
            i, value = parse_value_arg(args, i, arg)
            if value:
                json_path = value
        elif arg in ("--filter", "--backend"):
            i, value = parse_value_arg(args, i, arg)
            if value:
                query_string = value
        elif arg == "--first":
            i, first = parse_single_arg(args, i, arg, {"first"})
        elif arg == "--raw":
            i, raw = parse_single_arg(args, i, arg, {"raw"})
        else:
            print(f"Unknown argument: {arg}", file=sys.stderr)
            return "", None, None, None, None, None, {}, False, False, True

    return output_format, latitude, longitude, dir_path, json_path, query_string, attribute_search, first, raw, False


def _reverse_command(args: list[str]) -> bool:
    """Reverse geocode coordinates to address.

    Args:
        args: Command arguments.

    Returns:
        True if command executed successfully, False otherwise.
    """
    (
        output_format,
        latitude,
        longitude,
        dir_path,
        json_path,
        query_string,
        attribute_search,
        first,
        raw,
        has_error,
    ) = _parse_all_args(args)

    if has_error:
        return False

    if latitude is None or longitude is None:
        print("Error: --lat and --lon are required", file=sys.stderr)
        return False

    lib_name = _get_package_name()

    providers_args: dict[str, Any] = {
        "format": output_format,
        "json": json_path,
        "lib_name": lib_name,
        "dir_path": dir_path,
        "query_string": query_string,
    }

    if attribute_search:
        providers_args["attribute_search"] = attribute_search

    additional_args: dict[str, Any] = {"latitude": str(latitude), "longitude": str(longitude)}
    if raw:
        additional_args["raw"] = True

    pvk = get_providerkit(**providers_args)
    pvk.execute_providers("reverse_geocode", first=first, lib_name=lib_name, **providers_args, **additional_args)

    results = pvk.get_service_result("reverse_geocode")
    if not results:
        print("No results")
        return True

    if first and results:
        provider_result = results[0]
        if "error" in provider_result:
            print(f"Error: {provider_result['error']}", file=sys.stderr)
            return False
        provider = provider_result["provider"]
        result = provider.call_service("reverse_geocode", latitude=latitude, longitude=longitude, **additional_args)
        print(result)
        return True

    for provider_result in results:
        if "error" in provider_result:
            continue
        provider = provider_result["provider"]
        result = provider.call_service("reverse_geocode", latitude=latitude, longitude=longitude, **additional_args)
        print(result)

    return True


reverse_command = Command(_reverse_command, "Reverse geocode coordinates (use --lat latitude --lon longitude)")
