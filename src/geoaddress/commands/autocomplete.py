"""Address command for searching addresses."""

from __future__ import annotations

from providerkit.commands.provider import _PROVIDER_COMMAND_CONFIG
from qualitybase.commands import parse_args_from_config
from qualitybase.commands.base import Command
from qualitybase.services.utils import print_header, print_separator

from geoaddress.helpers import addresses_autocomplete

_ARG_CONFIG = {
    **_PROVIDER_COMMAND_CONFIG,
    'query': {'type': str, 'default': ''},
}


def _autocomplete_command(args: list[str]) -> bool:
    parsed = parse_args_from_config(args, _ARG_CONFIG, prog='address')
    kwargs = {}
    kwargs['attribute_search'] = parsed.get('attr', {}).get('kwargs', {})
    output_format = parsed.get('format', 'terminal')
    raw = parsed.get('raw', False)
    query = parsed.pop('query')
    first = parsed.pop('first', False)
    pvs_addresses = addresses_autocomplete(query, first=first, **kwargs)
    for pv in pvs_addresses:
        name = pv['provider'].name
        time = pv['response_time']
        print_separator()
        print_header(f"{name} - {time}s")
        print_separator()
        print(pv['provider'].response('addresses_autocomplete', raw, output_format))
    return True


autocomplete_command = Command(_autocomplete_command, "Autocomplete addresses (use --query query_string)")
