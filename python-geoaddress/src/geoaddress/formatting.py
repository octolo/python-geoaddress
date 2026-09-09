"""Format stored address data using GEOADDRESS_FIELDS_FORMATS layouts."""

from __future__ import annotations

from typing import Any, Union

DEFAULT_DISPLAY = "text_3lines"
DISPLAY_ALIASES = {
    "full": "text_full",
    "2lines": "text_2lines",
    "2 lines": "text_2lines",
    "3lines": "text_3lines",
    "3 lines": "text_3lines",
    "aligned": "text_aligned",
}
FormatConfig = list[Any]
DisplaySpec = Union[str, FormatConfig]


def _formats() -> dict[str, FormatConfig]:
    from geoaddress import GEOADDRESS_FIELDS_FORMATS

    return GEOADDRESS_FIELDS_FORMATS


def resolve_display(display: DisplaySpec = DEFAULT_DISPLAY) -> FormatConfig:
    """Return a format table from a display name or a custom layout."""
    if isinstance(display, list):
        return display
    formats = _formats()
    key = DISPLAY_ALIASES.get(display, display)
    try:
        return list(formats[key])
    except KeyError as exc:
        known = ", ".join(sorted(formats) + sorted(DISPLAY_ALIASES))
        raise ValueError(f"Unknown geoaddress display {display!r}. Expected one of: {known}") from exc


def format_address_lines(
    data: dict[str, Any] | None,
    display: DisplaySpec = DEFAULT_DISPLAY,
    *,
    separator: str = ", ",
) -> list[str]:
    """Join address fields per layout line.

    A flat list of strings is one concatenated line (``text_full``, ``city_line``).
    A list of lists is one concatenated line per inner list (``text_2lines``,
    ``text_3lines``). Mixed layouts (``text_aligned``) yield one line per
    top-level item. Nested format names are resolved from
    ``GEOADDRESS_FIELDS_FORMATS``.
    """
    if not data:
        return []
    return _format_config(data, resolve_display(display), separator, set())


def format_address_text(
    data: dict[str, Any] | None,
    display: DisplaySpec = DEFAULT_DISPLAY,
    *,
    separator: str = ", ",
    line_separator: str = "\n",
) -> str:
    """Return formatted address lines joined by ``line_separator``."""
    return line_separator.join(format_address_lines(data, display, separator=separator))


def _format_config(
    data: dict[str, Any],
    config: FormatConfig,
    separator: str,
    seen: set[str],
) -> list[str]:
    if not config:
        return []
    if all(isinstance(item, str) for item in config):
        line = _concat_items(data, config, separator, seen)
        return [line] if line else []

    lines: list[str] = []
    for item in config:
        if isinstance(item, (list, tuple)):
            line = _concat_items(data, item, separator, seen)
        else:
            line = _concat_items(data, [item], separator, seen)
        if line:
            lines.append(line)
    return lines


def _concat_items(
    data: dict[str, Any],
    items: list[Any] | tuple[Any, ...],
    separator: str,
    seen: set[str],
) -> str:
    parts: list[str] = []
    for item in items:
        if not isinstance(item, str):
            nested = _format_config(data, list(item), separator, seen)
            parts.extend(nested)
            continue
        formats = _formats()
        if item in formats:
            if item in seen:
                continue
            nested = _format_config(data, list(formats[item]), separator, seen | {item})
            parts.extend(nested)
            continue
        value = data.get(item)
        if value not in (None, ""):
            parts.append(str(value))
    return separator.join(parts)
