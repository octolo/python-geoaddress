"""Address command for searching addresses."""

from __future__ import annotations

from qualitybase.commands.base import Command
from qualitybase.services.utils import print_header, print_separator
from geoaddress.helpers import search_addresses
from qualitybase.commands import parse_args_from_config
from providerkit.commands.provider import _PROVIDER_COMMAND_CONFIG

_ARG_CONFIG = {
    **_PROVIDER_COMMAND_CONFIG,
    'query': {'type': str, 'default': ''},
}


def _address_command(args: list[str]) -> bool:
    parsed = parse_args_from_config(args, _ARG_CONFIG, prog='address')
    kwargs = {}
    kwargs['attribute_search'] = parsed.get('attr', {}).get('kwargs', {})
    output_format = parsed.get('format', 'terminal')
    raw = parsed.get('raw', False)
    query = parsed.pop('query')
    pvs_addresses = search_addresses(query, **kwargs)
    for pv in pvs_addresses:
        print_separator()
        print_header(pv['provider'].name)
        print_separator()
        print(pv['provider'].response('search_addresses', raw, output_format))
    return True


address_command = Command(_address_command, "Search addresses (use --query query_string)")
