"""Tests for postal address normalization and comparison."""

import pytest

from geoaddress import address_key, normalize_address


def test_normalize_address_preserves_display_case_and_metadata() -> None:
    """Keep postal labels readable and leave provider metadata untouched."""
    data = {
        'address_line1': ' 12  Rue de la Paix ',
        'locality': ' Le\u00a0Petit Bourg ',
        'postal_code': ' 01230 ',
        'country': ' France ',
        'country_code': ' fr ',
        'state_code': ' fr-ara ',
        'latitude': 0.0,
        'reference': ' Provider ID ',
    }

    normalized = normalize_address(data)

    assert normalized == {
        'address_line1': '12 Rue de la Paix',
        'locality': 'Le Petit Bourg',
        'postal_code': '01230',
        'country': 'France',
        'country_code': 'FR',
        'state_code': 'FR-ARA',
        'latitude': 0.0,
        'reference': ' Provider ID ',
    }
    assert data['country_code'] == ' fr '
    assert normalize_address(normalized) == normalized


def test_address_key_ignores_provider_presentation() -> None:
    """Match provider responses that differ only in presentation."""
    first = {
        'address_line1': '12 Stra\u00dfe des \u00c9coles',
        'country_code': ' DE ',
        'country': 'Germany',
        'latitude': 52.51,
        'backend': 'one',
        'postal_code': '10115',
    }
    second = {
        'postal_code': 10115,
        'address_line1': ' 12  STRASSE DES E\u0301COLES ',
        'address_line2': '\t',
        'country_code': 'de',
        'country': 'Deutschland',
        'latitude': 52.52,
        'backend': 'two',
    }

    assert address_key(first) == address_key(second)


@pytest.mark.parametrize(
    ('field', 'first', 'second'),
    [
        ('address_line1', '12 bis rue du Port', '12 rue du Port'),
        ('address_line1', 'Rue de l\u2019\u00c9glise', 'Rue de l\u2019Eglise'),
        ('address_line1', 'Rue Saint-Paul', 'Rue Saint Paul'),
        ('address_line2', 'Appt 4', 'Appt 5'),
        ('address_line2', 'Appt 4', None),
        ('locality', 'Le Petit Bourg', 'Le Grand Bourg'),
        ('postal_code', '01230', '1230'),
        ('country_code', 'FR', 'BE'),
        ('country', 'France', 'Belgique'),
    ],
)
def test_address_key_distinguishes_postal_details(
    field: str,
    first: str,
    second: str | None,
) -> None:
    """Keep meaningful postal differences in the comparison key."""
    assert address_key({field: first}) != address_key({field: second})


def test_address_key_uses_country_name_only_without_code() -> None:
    """Do not infer a country code from a country name."""
    assert address_key({'country': ' France '}) == address_key(
        {'country': 'FRANCE', 'country_code': None},
    )
    assert address_key({'country': 'France'}) != address_key(
        {'country': 'France', 'country_code': 'FR'},
    )


def test_address_key_is_empty_without_postal_fields() -> None:
    """Do not derive a postal identity from provider coordinates."""
    assert address_key(None) == address_key({'latitude': 0, 'postal_code': ''})
    assert address_key(None) == ()


def test_address_key_rejects_non_scalar_postal_values() -> None:
    """Reject malformed postal values instead of dropping them."""
    with pytest.raises(TypeError, match='postal_code'):
        address_key({'postal_code': ['75001', '75002']})
