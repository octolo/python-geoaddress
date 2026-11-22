"""Normalize and compare structured postal addresses."""

from __future__ import annotations

from collections.abc import Mapping
from unicodedata import normalize

_POSTAL_FIELDS = (
    'address_line1',
    'address_line2',
    'address_line3',
    'number',
    'street',
    'po_box',
    'locality',
    'neighbourhood',
    'municipality',
    'city',
    'postal_code',
    'sorting_code',
    'county',
    'state',
    'state_code',
    'country_code',
    'country',
)
_CODE_FIELDS = frozenset({'country_code', 'state_code'})


def normalize_address(data: Mapping[str, object] | None) -> dict[str, object]:
    """Return a cleaned copy suitable for display or storage.

    Args:
        data: Structured address. None represents an empty address.

    Returns:
        A new dictionary with whitespace collapsed and Unicode composed (NFC)
        in postal text and the organization name. Country and subdivision
        codes are uppercased, not validated or inferred. Other text keeps its
        case. Non-string values and unrelated metadata are unchanged.
    """
    result = {} if data is None else dict(data)
    for field in (*_POSTAL_FIELDS, 'organization'):
        value = result.get(field)
        if isinstance(value, str):
            text = normalize('NFC', ' '.join(value.split()))
            result[field] = text.upper() if field in _CODE_FIELDS else text
    return result


def address_key(
    data: Mapping[str, object] | None,
) -> tuple[tuple[str, str], ...]:
    """Build a hashable key for exact comparison after postal normalization.

    Args:
        data: Structured address. None represents an empty address.

    Returns:
        Postal field/value pairs in fixed order, with text case-folded and
        empty fields omitted. A country code takes precedence over the country
        name. Coordinates, organization name and provider metadata are not
        part of the key. An empty key does not identify a postal address.

    Raises:
        TypeError: A compared postal field is neither text, an integer, nor
            None.
    """
    address = normalize_address(data)
    key = {}
    for field in _POSTAL_FIELDS:
        if field == 'country' and 'country_code' in key:
            continue
        text = _comparison_text(field, address.get(field))
        if text:
            key[field] = text
    return tuple(key.items())


def _comparison_text(field: str, value: object) -> str:
    if value is None:
        return ''
    if isinstance(value, str):
        return normalize('NFC', value.casefold())
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    message = f'Postal field {field!r} must be a string, integer, or None'
    raise TypeError(message)
