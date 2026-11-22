"""Tests for the configurable address flag URL."""

import pytest
from django.test import override_settings
from django.urls import reverse

from django_geoaddress.fields import (
    GeoaddressAutocompleteWidget,
    GeoaddressValue,
)


def local_flag_url(country_code: str) -> str:
    """Build a local flag URL from the country code."""
    return f'/static/flags/{country_code}.png'


def test_flag_url_defaults_to_flagcdn() -> None:
    """Use FlagCDN when no processor has been configured."""
    address = GeoaddressValue({'country_code': 'FR'})

    assert address.flag_url == 'https://flagcdn.com/fr.svg'


@pytest.mark.parametrize(
    ('processor', 'country_code', 'expected'),
    [
        (None, 'FR', None),
        (
            'django_geoaddress.processors.flagcdn_url',
            ' fr ',
            'https://flagcdn.com/fr.svg',
        ),
        (
            'django_geoaddress.processors.flagcdn_url',
            'uk',
            'https://flagcdn.com/gb.svg',
        ),
        ('tests.test_flag_url.local_flag_url', ' ca ', '/static/flags/CA.png'),
        ('tests.test_flag_url.local_flag_url', '../fr', None),
        ('tests.test_flag_url.local_flag_url', None, None),
    ],
)
def test_flag_url(
    processor: str | None,
    country_code: str | None,
    expected: str | None,
) -> None:
    """Override or disable the processor without altering the data."""
    data = {'country_code': country_code}
    address = GeoaddressValue(data)

    with override_settings(GEOADDRESS_FLAG_URL_PROCESSOR=processor):
        assert address.flag_url == expected

    assert dict(address) == data


@pytest.mark.parametrize('readonly', [False, True])
def test_widget_displays_configured_flag(readonly: bool) -> None:
    """Render the flag for editable and read-only addresses."""
    widget = GeoaddressAutocompleteWidget(
        attrs={'readonly': readonly},
    )
    with override_settings(
        GEOADDRESS_FLAG_URL_PROCESSOR='tests.test_flag_url.local_flag_url',
    ):
        html = widget.render('address', {'country_code': 'fr'})

    assert 'src="/static/flags/FR.png"' in html
    assert 'data-flag-url="/django_geoaddress/flag-url/"' in html
    assert 'geoaddress-autocomplete-input-with-flag' in html
    assert (
        html.index('geoaddress-autocomplete-input-with-flag')
        < html.index('geoaddress-autocomplete-flag')
        < html.index('geoaddress-autocomplete-icons')
    )


def test_widget_flag_is_absent_when_disabled() -> None:
    """Do not render the flag or lookup endpoint when explicitly disabled."""
    widget = GeoaddressAutocompleteWidget()

    with override_settings(GEOADDRESS_FLAG_URL_PROCESSOR=None):
        html = widget.render('address', {'country_code': 'fr'})

    assert 'geoaddress-autocomplete-flag' not in html
    assert 'data-flag-url' not in html


def test_widget_without_country_has_hidden_flag() -> None:
    """Allow a flag to appear later without initially loading an image."""
    html = GeoaddressAutocompleteWidget().render('address', {})

    assert 'geoaddress-autocomplete-flag geoaddress-autocomplete-hidden' in html
    assert 'data-flag-url="/django_geoaddress/flag-url/"' in html


def test_flag_url_endpoint_uses_configured_processor(client) -> None:
    """Resolve edited codes with the same processor as the initial render."""
    url = reverse('django_geoaddress:flag_url')

    with override_settings(
        GEOADDRESS_FLAG_URL_PROCESSOR='tests.test_flag_url.local_flag_url',
    ):
        response = client.get(url, {'country_code': ' ca '})
        invalid = client.get(url, {'country_code': '../ca'})

    assert response.json() == {'flag_url': '/static/flags/CA.png'}
    assert invalid.json() == {'flag_url': None}


def test_flag_url_endpoint_respects_disabled_setting(client) -> None:
    """Keep dynamic lookups disabled when the processor is disabled."""
    with override_settings(GEOADDRESS_FLAG_URL_PROCESSOR=None):
        response = client.get(
            reverse('django_geoaddress:flag_url'),
            {'country_code': 'FR'},
        )

    assert response.json() == {'flag_url': None}
