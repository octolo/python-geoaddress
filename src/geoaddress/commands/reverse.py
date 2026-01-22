"""Reverse geocode command for getting address from coordinates."""

from __future__ import annotations

import sys

from providerkit.commands.provider import _PROVIDER_COMMAND_CONFIG
from qualitybase.commands import parse_args_from_config
from qualitybase.commands.base import Command
from qualitybase.services.utils import print_header, print_separator

from geoaddress.helpers import reverse_geocode

_ARG_CONFIG = {
    **_PROVIDER_COMMAND_CONFIG,
    'lat': {'type': float, 'default': None},
    'lon': {'type': float, 'default': None},
    'latitude': {'type': float, 'default': None},
    'longitude': {'type': float, 'default': None},
}


def _reverse_command(args: list[str]) -> bool:
    """Reverse geocode coordinates to address."""
    parsed = parse_args_from_config(args, _ARG_CONFIG, prog='reverse')
    latitude = parsed.get('latitude')
    if latitude is None:
        latitude = parsed.get('lat')
    longitude = parsed.get('longitude')
    if longitude is None:
        longitude = parsed.get('lon')

    if latitude is None or longitude is None:
        print("Error: --latitude and --longitude (or --lat and --lon) are required", file=sys.stderr)
        return False

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (ValueError, TypeError):
        print("Error: --latitude and --longitude must be valid numbers", file=sys.stderr)
        return False

    kwargs = {}
    kwargs['attribute_search'] = parsed.get('attr', {}).get('kwargs', {})
    output_format = parsed.get('format', 'terminal')
    raw = parsed.get('raw', False)
    pvs_addresses = reverse_geocode(latitude, longitude, **kwargs)
    for pv in pvs_addresses:
        name = pv['provider'].name
        time = pv['response_time']
        print_separator()
        print_header(f"{name} - {time}s")
        print_separator()
        print(pv['provider'].response('reverse_geocode', raw, output_format))
    return True

reverse_command = Command(_reverse_command, "Reverse geocode coordinates to address (use --latitude latitude --longitude longitude)")
