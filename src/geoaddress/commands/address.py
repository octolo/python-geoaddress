"""Address command for searching addresses."""

from __future__ import annotations  # noqa: I001

import sys
from typing import TYPE_CHECKING, Any

from qualitybase.commands.base import Command

from geoaddress.helpers import search_addresses

if TYPE_CHECKING:
    from pathlib import Path


def _address_command(args: list[str]) -> bool:  # noqa: C901
    """Search addresses.

    Args:
        args: Command arguments.

    Returns:
        True if command executed successfully, False otherwise.
    """
    output_format = "table"
    dir_path: str | Path | None = None
    json_path: str | Path | None = None
    query_string: str | None = None
    query: str | None = None
    first: bool = False
    raw: bool = False
    additional_args: dict[str, str | bool] = {}
    attribute_search: dict[str, str] = {}

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--query" and i + 1 < len(args):
            query = args[i + 1]
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

    if not query:
        print("Error: --query is required", file=sys.stderr)
        return False

    providers_args: dict[str, Any] = {
        "format": output_format,
        "json": json_path,
        "dir_path": dir_path,
        "query_string": query_string,
    }

    if attribute_search:
        providers_args["attribute_search"] = attribute_search

    if raw:
        additional_args["raw"] = True


    result = search_addresses(query=query, first=first, additional_args=additional_args, **providers_args)

    print(result)
    return True


address_command = Command(_address_command, "Search addresses (use --query query_string)")
