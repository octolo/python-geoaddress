"""Reverse geocode command for getting address from coordinates."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Any

from qualitybase.cli import _get_package_name  # noqa: TID252
from providerkit.helpers import try_providers, try_providers_first  # noqa: TID252
from qualitybase.commands.base import Command

if TYPE_CHECKING:
    from pathlib import Path


def _reverse_command(args: list[str]) -> bool:  # noqa: C901
    """Reverse geocode coordinates to address.

    Args:
        args: Command arguments.

    Returns:
        True if command executed successfully, False otherwise.
    """
    output_format = "table"
    dir_path: str | Path | None = None
    json_path: str | Path | None = None
    query_string: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    first: bool = False
    raw: bool = False
    additional_args: dict[str, str | bool] = {}
    attribute_search: dict[str, str] = {}

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--lat" and i + 1 < len(args):
            try:
                latitude = float(args[i + 1])
            except ValueError:
                print(f"Error: Invalid latitude value: {args[i + 1]}", file=sys.stderr)
                return False
            i += 2
        elif arg == "--lon" and i + 1 < len(args):
            try:
                longitude = float(args[i + 1])
            except ValueError:
                print(f"Error: Invalid longitude value: {args[i + 1]}", file=sys.stderr)
                return False
            i += 2
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

    additional_args["latitude"] = str(latitude)
    additional_args["longitude"] = str(longitude)
    if raw:
        additional_args["raw"] = True
    providers_args["additional_args"] = additional_args

    if first:
        result = try_providers_first(
            command="reverse_geocode",
            **providers_args,
        )
    else:
        result = try_providers(
            command="reverse_geocode",
            **providers_args,
        )

    print(result)
    return True


reverse_command = Command(_reverse_command, "Reverse geocode coordinates (use --lat latitude --lon longitude)")
