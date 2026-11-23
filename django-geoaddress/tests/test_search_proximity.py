"""Tests for proximity parameters on the address search endpoint."""

from unittest.mock import Mock

import providerkit.helpers
import pytest
import requests
from django.test import override_settings
from django.urls import reverse
from geoaddress.providers.nominatim import NominatimProvider


@override_settings(GEOADDRESS_ADDRESSVIEW_AUTH=False)
def test_search_passes_proximity_to_provider(client, monkeypatch) -> None:
    """Forward the requested radius through the manager to the provider."""
    provider = NominatimProvider()
    monkeypatch.setattr(
        providerkit.helpers,
        'get_providers',
        lambda **_: [provider],
    )
    response = Mock()
    response.json.return_value = []
    request = Mock(return_value=response)
    monkeypatch.setattr(requests, 'get', request)

    result = client.get(
        reverse('django_geoaddress:search_addresses'),
        {
            'q': 'Paris',
            'format': 'json',
            'bck': 'nominatim',
            'proximity': '48.8566,2.3522',
            'proximity_radius_km': '1',
        },
    )

    assert result.status_code == 200
    _, south, _, north = map(
        float,
        request.call_args.kwargs['params']['viewbox'].split(','),
    )
    assert (north - south) / 2 == pytest.approx(1 / 111.195, rel=0.001)
    assert result.json() == {'addresses': [], 'count': 0}


@override_settings(GEOADDRESS_ADDRESSVIEW_AUTH=False)
def test_search_default_radius_and_no_proximity(client, monkeypatch) -> None:
    """Use the provider default, and leave unrelated searches unchanged."""
    provider = NominatimProvider()
    monkeypatch.setattr(
        providerkit.helpers,
        'get_providers',
        lambda **_: [provider],
    )
    response = Mock()
    response.json.return_value = []
    request = Mock(return_value=response)
    monkeypatch.setattr(requests, 'get', request)
    url = reverse('django_geoaddress:search_addresses')

    biased = client.get(
        url,
        {
            'q': 'Paris',
            'format': 'json',
            'proximity': '48.8566,2.3522',
        },
    )
    _, south, _, north = map(
        float,
        request.call_args.kwargs['params']['viewbox'].split(','),
    )
    unbiased = client.get(url, {'q': 'Paris', 'format': 'json'})

    assert biased.status_code == unbiased.status_code == 200
    assert (north - south) / 2 == pytest.approx(100 / 111.195, rel=0.001)
    assert 'viewbox' not in request.call_args.kwargs['params']


@pytest.mark.parametrize(
    'params',
    [
        {'proximity': 'Paris'},
        {'proximity': '91,0'},
        {'proximity': '0,181'},
        {'proximity': 'nan,0'},
        {'proximity': '0,0', 'proximity_radius_km': 'abc'},
        {'proximity': '0,0', 'proximity_radius_km': '0'},
        {'proximity': '0,0', 'proximity_radius_km': '-1'},
        {'proximity': '0,0', 'proximity_radius_km': 'inf'},
        {'proximity': '48,2', 'proximity_radius_km': '1e-300'},
        {'proximity': 'None', 'proximity_radius_km': '-1'},
        {'proximity_radius_km': 'abc'},
    ],
)
@override_settings(GEOADDRESS_ADDRESSVIEW_AUTH=False)
def test_search_rejects_invalid_proximity(client, monkeypatch, params) -> None:
    """Return a client error without invoking providers for invalid values."""
    request = Mock()
    monkeypatch.setattr(requests, 'get', request)

    result = client.get(
        reverse('django_geoaddress:search_addresses'),
        {'q': 'Paris', 'format': 'json', **params},
    )

    assert result.status_code == 400
    assert 'error' in result.json()
    request.assert_not_called()


@pytest.mark.parametrize('empty', ['', '   ', 'None', ' null '])
@override_settings(GEOADDRESS_ADDRESSVIEW_AUTH=False)
def test_empty_proximity_does_not_apply_radius(
    client, monkeypatch, empty
) -> None:
    """Treat empty proximity as absent even with a configured radius."""
    provider = NominatimProvider()
    monkeypatch.setattr(
        providerkit.helpers,
        'get_providers',
        lambda **_: [provider],
    )
    response = Mock()
    response.json.return_value = []
    request = Mock(return_value=response)
    monkeypatch.setattr(requests, 'get', request)

    result = client.get(
        reverse('django_geoaddress:search_addresses'),
        {
            'q': 'Paris',
            'format': 'json',
            'proximity': empty,
            'proximity_radius_km': '1',
        },
    )

    assert result.status_code == 200
    assert 'viewbox' not in request.call_args.kwargs['params']


@pytest.mark.parametrize('empty', ['', '   ', 'None', ' null '])
@override_settings(GEOADDRESS_ADDRESSVIEW_AUTH=False)
def test_empty_radius_uses_provider_default(client, monkeypatch, empty) -> None:
    """Use the default radius when a location is provided without a radius."""
    provider = NominatimProvider()
    monkeypatch.setattr(
        providerkit.helpers,
        'get_providers',
        lambda **_: [provider],
    )
    response = Mock()
    response.json.return_value = []
    request = Mock(return_value=response)
    monkeypatch.setattr(requests, 'get', request)

    result = client.get(
        reverse('django_geoaddress:search_addresses'),
        {
            'q': 'Paris',
            'format': 'json',
            'proximity': '48.8566,2.3522',
            'proximity_radius_km': empty,
        },
    )

    assert result.status_code == 200
    _, south, _, north = map(
        float,
        request.call_args.kwargs['params']['viewbox'].split(','),
    )
    assert (north - south) / 2 == pytest.approx(100 / 111.195, rel=0.001)


@override_settings(GEOADDRESS_ADDRESSVIEW_AUTH=False)
def test_radius_without_proximity_is_not_applied(client, monkeypatch) -> None:
    """A radius alone does not impose a geographical preference."""
    provider = NominatimProvider()
    monkeypatch.setattr(
        providerkit.helpers,
        'get_providers',
        lambda **_: [provider],
    )
    response = Mock()
    response.json.return_value = []
    request = Mock(return_value=response)
    monkeypatch.setattr(requests, 'get', request)

    result = client.get(
        reverse('django_geoaddress:search_addresses'),
        {'q': 'Paris', 'format': 'json', 'proximity_radius_km': '1'},
    )

    assert result.status_code == 200
    assert 'viewbox' not in request.call_args.kwargs['params']
