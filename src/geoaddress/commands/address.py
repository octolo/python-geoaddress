"""Address command for searching addresses."""

from __future__ import annotations

from qualitybase.commands.base import Command
from geoaddress.helpers import search_addresses


def _address_command(args: list[str]) -> bool:
    addresses = search_addresses("1600 Amphitheatre Parkway, Mountain View, CA")
    
    return True


address_command = Command(_address_command, "Search addresses (use --query query_string)")
