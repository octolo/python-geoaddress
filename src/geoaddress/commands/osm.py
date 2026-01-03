"""OSM command for searching addresses by OSM key-value pairs."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from qualitybase.cli import _get_package_name  # noqa: TID252
from providerkit.helpers import try_providers, try_providers_first  # noqa: TID252
from qualitybase.commands.base import Command

if TYPE_CHECKING:
    from pathlib import Path


def _osm_command(args: list[str]) -> bool:  # noqa: C901
    """Get address by OSM key-value pairs.

    Args:
        args: Command arguments.

    Returns:
        True if command executed successfully, False otherwise.
    """
    output_format = "table"
    dir_path: str | Path | None = None
    json_path: str | Path | None = None
    query_string: str | None = None
    osm_keys_value: dict[str, Any] = {}
    first: bool = False
    raw: bool = False
    additional_args: dict[str, Any] = {}
    attribute_search: dict[str, str] = {}
    osm_id: str | None = None
    osm_type: str | None = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--osm-id" and i + 1 < len(args):
            osm_id = args[i + 1]
            i += 2
        elif arg == "--osm-type" and i + 1 < len(args):
            osm_type = args[i + 1]
            i += 2
        elif arg == "--tag":
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                tag_arg = args[i]
                if "=" in tag_arg:
                    key, value = tag_arg.split("=", 1)
                    osm_keys_value[key] = value
                else:
                    print(f"Invalid tag format: {tag_arg}. Expected format: key=value", file=sys.stderr)
                    return False
                i += 1
        elif arg == "--attr":
            i += 1
            while i < len(args) and not args[i].startswith("--"):
                attr_arg = args[i]
                if "=" in attr_arg:
                    key, value = attr_arg.split("=", 1)
                    attribute_search[key] = value
                else:
                    print(f"Invalid attribute format: {attr_arg}. Expected format: key=value", file=sys.stderr)
                    return False
                i += 1
        elif arg == "--format" and i + 1 < len(args):
            output_format = args[i + 1]
            i += 2
        elif arg == "--dir" and i + 1 < len(args):
            dir_path = args[i + 1]
            i += 2
        elif arg == "--json" and i + 1 < len(args):
            json_path = args[i + 1]
            i += 2
        elif arg == "--filter" or arg == "--backend":
            query_string = args[i + 1]
            i += 2
        elif arg == "--first":
            first = True
            i += 1
        elif arg == "--raw":
            raw = True
            i += 1
        else:
            print(f"Unknown argument: {arg}", file=sys.stderr)
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

    additional_args["osm_keys_value"] = osm_keys_value
    if raw:
        additional_args["raw"] = True
    providers_args["additional_args"] = additional_args

    if first:
        result = try_providers_first(
            command="get_address_by_osm",
            **providers_args,
        )
    else:
        result = try_providers(
            command="get_address_by_osm",
            **providers_args,
        )

    print(result)
    return True


osm_command = Command(_osm_command, "Get address by OSM key-value pairs (use --tag key=value) or OSM ID (use --osm-id id --osm-type type)")

