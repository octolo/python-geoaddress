"""Reference command for getting address by reference."""

from __future__ import annotations  # noqa: I001

import sys
from typing import TYPE_CHECKING, Any

from qualitybase.commands.base import Command

from geoaddress.helpers import get_address_by_reference

if TYPE_CHECKING:
    from pathlib import Path


def _reference_command(args: list[str]) -> bool:  # noqa: C901
    """Get address by reference.

    Args:
        args: Command arguments.

    Returns:
        True if command executed successfully, False otherwise.
    """
    output_format = "table"
    dir_path: str | Path | None = None
    json_path: str | Path | None = None
    query_string: str | None = None
    reference: str | None = None
    first: bool = False
    raw: bool = False
    additional_args: dict[str, str | bool] = {}
    attribute_search: dict[str, str] = {}

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--ref" and i + 1 < len(args):
            reference = args[i + 1]
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

    if not reference:
        print("Error: --ref is required", file=sys.stderr)
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

    result = get_address_by_reference(reference=reference, first=first, additional_args=additional_args, **providers_args)

    print(result)
    return True


reference_command = Command(_reference_command, "Get address by reference (use --ref reference_id)")
