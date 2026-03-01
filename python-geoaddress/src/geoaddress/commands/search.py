"""Address command for searching addresses."""

from __future__ import annotations

from clicommands.commands.args import parse_args_from_config
from clicommands.commands.base import Command
from clicommands.utils import print_header, print_separator
from providerkit.commands.provider import _PROVIDER_COMMAND_CONFIG

from geoaddress.helpers import search_addresses

_ARG_CONFIG = {
    **_PROVIDER_COMMAND_CONFIG,
    'query': {'type': str, 'default': ''},
}


def _search_command(args: list[str]) -> bool:
    parsed = parse_args_from_config(args, _ARG_CONFIG, prog='address')
    kwargs = {}
    attr_value = parsed.get('attr', {})
    if isinstance(attr_value, dict):
        kwargs['attribute_search'] = attr_value.get('kwargs', {})
    output_format = parsed.get('format', 'terminal')
    raw = parsed.get('raw', False)
    query = parsed.pop('query')
    first = parsed.pop('first', False)
    pvs_addresses = search_addresses(query, first=first, **kwargs)
    for pv in pvs_addresses:
        name = pv['provider'].name
        time = pv['response_time']
        print_separator()
        print_header(f"{name} - {time}s")
        print_separator()
        print(pv['provider'].response('search_addresses', raw=raw, output_format=output_format))
    return True


search_command = Command(_search_command, "Search addresses (use --query query_string)")
