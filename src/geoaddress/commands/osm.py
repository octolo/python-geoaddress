"""OSM command for searching addresses by OSM key-value pairs."""

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
) -> tuple[str, str | None, str | None, str | None, str | None, str | None, dict[str, str], bool, bool, dict[str, Any], bool]:
    """Parse all command line arguments."""
    output_format = "table"
    osm_id: str | None = None
    osm_type: str | None = None
    dir_path: str | Path | None = None
    json_path: str | Path | None = None
    query_string: str | None = None
    osm_keys_value: dict[str, Any] = {}
    attribute_search: dict[str, str] = {}
    first: bool = False
    raw: bool = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--osm-id":
            i, value = parse_value_arg(args, i, arg)
            if value:
                osm_id = value
        elif arg == "--osm-type":
            i, value = parse_value_arg(args, i, arg)
            if value:
                osm_type = value
        elif arg == "--tag":
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                tag_arg = args[i]
                if "=" in tag_arg:
                    key, value = tag_arg.split("=", 1)
                    osm_keys_value[key] = value
                else:
                    print(f"Invalid tag format: {tag_arg}. Expected format: key=value", file=sys.stderr)
                    return "", None, None, None, None, None, {}, False, False, {}, True
                i += 1
        elif arg == "--attr":
            result = parse_attr_args(args, i, attribute_search)
            if result is None:
                return "", None, None, None, None, None, {}, False, False, {}, True
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
            return "", None, None, None, None, None, {}, False, False, {}, True

    return output_format, osm_id, osm_type, dir_path, json_path, query_string, attribute_search, first, raw, osm_keys_value, False


def _osm_command(args: list[str]) -> bool:
    """Get address by OSM key-value pairs.

    Args:
        args: Command arguments.

    Returns:
        True if command executed successfully, False otherwise.
    """
    (
        output_format,
        osm_id,
        osm_type,
        dir_path,
        json_path,
        query_string,
        attribute_search,
        first,
        raw,
        osm_keys_value,
        has_error,
    ) = _parse_all_args(args)

    if has_error:
        return False

    if osm_id or osm_type:
        if not osm_id or not osm_type:
            print("Error: Both --osm-id and --osm-type are required when using OSM ID lookup", file=sys.stderr)
            return False
        try:
            osm_keys_value = {"osm_id": int(osm_id), "osm_type": osm_type}
        except ValueError:
            print(f"Error: Invalid OSM ID format: {osm_id}", file=sys.stderr)
            return False
    elif not osm_keys_value:
        print("Error: Either --osm-id and --osm-type, or at least one --tag key=value is required", file=sys.stderr)
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

    additional_args: dict[str, Any] = {"osm_keys_value": osm_keys_value}
    if raw:
        additional_args["raw"] = True

    pvk = get_providerkit(**providers_args)
    pvk.execute_providers("get_address_by_osm", first=first, lib_name=lib_name, **providers_args, **additional_args)

    results = pvk.get_service_result("get_address_by_osm")
    if not results:
        print("No results")
        return True

    if first and results:
        provider_result = results[0]
        if "error" in provider_result:
            print(f"Error: {provider_result['error']}", file=sys.stderr)
            return False
        provider = provider_result["provider"]
        result = provider.call_service("get_address_by_osm", osm_keys_value=osm_keys_value, **additional_args)
        print(result)
        return True

    for provider_result in results:
        if "error" in provider_result:
            continue
        provider = provider_result["provider"]
        result = provider.call_service("get_address_by_osm", osm_keys_value=osm_keys_value, **additional_args)
        print(result)

    return True


osm_command = Command(_osm_command, "Get address by OSM key-value pairs (use --tag key=value) or OSM ID (use --osm-id id --osm-type type)")

