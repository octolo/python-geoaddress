"""Built-in processors for computed address values."""


def flagcdn_url(country_code: str) -> str:
    """Build an SVG flag URL using FlagCDN.

    Args:
        country_code: Uppercase two-letter country code.

    Returns:
        The flag URL. The common UK alias resolves to GB.
    """
    code = 'gb' if country_code == 'UK' else country_code.lower()
    return f'https://flagcdn.com/{code}.svg'
