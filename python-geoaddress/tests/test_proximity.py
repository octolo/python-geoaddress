"""Tests for provider-specific proximity bias parameters."""

from math import cos, radians
from unittest.mock import Mock

import providerkit.helpers
import pytest
import requests
from geoaddress.helpers import addresses_autocomplete, search_addresses
from geoaddress.providers.geoapify import GeoapifyProvider
from geoaddress.providers.geocode_earth import GeocodeEarthProvider
from geoaddress.providers.google import GoogleMapsProvider
from geoaddress.providers.locationiq import LocationIQProvider
from geoaddress.providers.mapbox import MapboxProvider
from geoaddress.providers.maps_co import MapsCoProvider
from geoaddress.providers.nominatim import NominatimProvider
from geoaddress.providers.opencage import OpencageProvider
from geoaddress.providers.photon import PhotonProvider


@pytest.mark.parametrize(
    ('provider_class', 'parameter', 'expected'),
    [
        (PhotonProvider, 'lat', '48.8566'),
        (MapboxProvider, 'proximity', '2.3522,48.8566'),
        (GeoapifyProvider, 'bias', 'proximity:2.3522,48.8566'),
        (OpencageProvider, 'proximity', '48.8566,2.3522'),
        (GeocodeEarthProvider, 'focus.point.lat', '48.8566'),
    ],
)
@pytest.mark.parametrize(
    'method', ['search_addresses', 'addresses_autocomplete']
)
def test_native_proximity_is_forwarded(
    monkeypatch,
    provider_class,
    parameter: str,
    expected: str,
    method: str,
) -> None:
    """Keep the native provider's proximity parameter and result order."""
    provider = provider_class()
    monkeypatch.setattr(provider, '_api_key', 'test', raising=False)
    monkeypatch.setattr(provider, '_access_token', 'test', raising=False)
    response = Mock()
    response.json.return_value = {
        'features': [{'id': 'first'}, {'id': 'second'}],
        'results': [{'id': 'first'}, {'id': 'second'}],
    }
    request = Mock(return_value=response)
    monkeypatch.setattr(requests, 'get', request)

    results = getattr(provider, method)(
        'Paris',
        proximity='48.8566,2.3522',
    )

    assert request.call_args.kwargs['params'][parameter] == expected
    assert [item['id'] for item in results] == ['first', 'second']


@pytest.mark.parametrize(
    ('provider_class', 'parameter'),
    [
        (NominatimProvider, 'viewbox'),
        (LocationIQProvider, 'viewbox'),
        (MapsCoProvider, 'viewbox'),
        (GoogleMapsProvider, 'bounds'),
    ],
)
@pytest.mark.parametrize(
    'method', ['search_addresses', 'addresses_autocomplete']
)
@pytest.mark.parametrize('radius', [None, 25])
def test_proximity_uses_soft_box(
    monkeypatch,
    provider_class,
    parameter: str,
    method: str,
    radius: int | None,
) -> None:
    """Use a configurable soft box without excluding other results."""
    provider = provider_class()
    monkeypatch.setattr(provider, '_api_key', 'test', raising=False)
    response = Mock()
    response.json.return_value = (
        {'status': 'OK', 'results': [{'id': 'far'}, {'id': 'near'}]}
        if provider_class is GoogleMapsProvider
        else [{'id': 'far'}, {'id': 'near'}]
    )
    request = Mock(return_value=response)
    monkeypatch.setattr(requests, 'get', request)
    kwargs: dict[str, str | int] = {'proximity': '48.8566,2.3522'}
    if radius is not None:
        kwargs['proximity_radius_km'] = radius

    results = getattr(provider, method)('Paris', **kwargs)

    params = request.call_args.kwargs['params']
    if parameter == 'bounds':
        south_west, north_east = params[parameter].split('|')
        south, west = map(float, south_west.split(','))
        north, east = map(float, north_east.split(','))
    else:
        west, south, east, north = map(float, params[parameter].split(','))
    expected_radius = radius if radius is not None else 100
    assert (north - south) / 2 == pytest.approx(
        expected_radius / 111.195,
        rel=0.001,
    )
    assert (east - west) / 2 == pytest.approx(
        expected_radius / (111.195 * cos(radians(48.8566))),
        rel=0.001,
    )
    assert south < 48.8566 < north
    assert west < 2.3522 < east
    assert 'bounded' not in params
    assert 'lat' not in params
    assert 'lon' not in params
    assert 'location' not in params
    assert [item['id'] for item in results] == ['far', 'near']


@pytest.mark.parametrize(
    'proximity',
    ['89.9,5', '90,0', '-90,0', '0,179.9', '0,-179.9', '0,180'],
)
def test_viewbox_handles_poles_and_antimeridian(
    monkeypatch, proximity: str
) -> None:
    """Keep valid, non-crossing longitude bounds at geographic edges."""
    response = Mock()
    response.json.return_value = []
    request = Mock(return_value=response)
    monkeypatch.setattr(requests, 'get', request)

    NominatimProvider().search_addresses('Paris', proximity=proximity)

    west, south, east, north = map(
        float,
        request.call_args.kwargs['params']['viewbox'].split(','),
    )
    assert (west, east) == (-180, 180)
    assert -90 <= south < north <= 90


@pytest.mark.parametrize(
    ('proximity', 'radius'),
    [
        ('abc', 100),
        ('91,0', 100),
        ('0,181', 100),
        ('nan,0', 100),
        ('0,0', 0),
        ('0,0', -1),
        ('0,0', float('inf')),
        ('48,2', 1e-300),
    ],
)
def test_invalid_proximity_is_explicit(proximity: str, radius: float) -> None:
    """Reject invalid focus coordinates and box sizes before sending a request."""
    with pytest.raises(ValueError, match='proximity'):
        NominatimProvider().search_addresses(
            'Paris',
            proximity=proximity,
            proximity_radius_km=radius,
        )


@pytest.mark.parametrize(
    ('provider_class', 'parameter'),
    [
        (NominatimProvider, 'viewbox'),
        (LocationIQProvider, 'viewbox'),
        (MapsCoProvider, 'viewbox'),
        (GoogleMapsProvider, 'bounds'),
    ],
)
@pytest.mark.parametrize(
    'method', ['search_addresses', 'addresses_autocomplete']
)
def test_no_proximity_keeps_unbiased_request(
    monkeypatch,
    provider_class,
    parameter: str,
    method: str,
) -> None:
    """Omit the bias parameter when no location is given."""
    provider = provider_class()
    monkeypatch.setattr(provider, '_api_key', 'test', raising=False)
    response = Mock()
    response.json.return_value = {'status': 'OK', 'results': []}
    request = Mock(return_value=response)
    monkeypatch.setattr(requests, 'get', request)

    getattr(provider, method)('Paris')

    assert parameter not in request.call_args.kwargs['params']


@pytest.mark.parametrize('search', [search_addresses, addresses_autocomplete])
def test_public_api_forwards_configured_radius(monkeypatch, search) -> None:
    """Forward proximity and radius through ProviderKit to the provider."""
    provider = NominatimProvider()
    monkeypatch.setattr(
        providerkit.helpers, 'get_providers', lambda **_: [provider]
    )
    response = Mock()
    response.json.return_value = [{'id': 'first'}, {'id': 'second'}]
    request = Mock(return_value=response)
    monkeypatch.setattr(requests, 'get', request)

    results = search(
        'Paris',
        proximity='48.8566,2.3522',
        proximity_radius_km=25,
    )

    _, south, _, north = map(
        float,
        request.call_args.kwargs['params']['viewbox'].split(','),
    )
    assert (north - south) / 2 == pytest.approx(25 / 111.195, rel=0.001)
    assert [item['id'] for item in results[0]['result']] == ['first', 'second']


def test_public_api_reports_invalid_radius(monkeypatch) -> None:
    """Expose validation failures in the ProviderKit response."""
    provider = NominatimProvider()
    monkeypatch.setattr(
        providerkit.helpers, 'get_providers', lambda **_: [provider]
    )

    results = search_addresses(
        'Paris',
        proximity='48.8566,2.3522',
        proximity_radius_km=0,
    )

    assert 'proximity_radius_km' in results[0]['error']
