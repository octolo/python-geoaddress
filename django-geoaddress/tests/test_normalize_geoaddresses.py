"""Tests for the interactive postal address cleanup command."""

from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from tests.app.models import Location, LocationReadonly

DIRTY_ADDRESS = {
    'address_line1': ' 12  Rue de la Paix ',
    'country_code': ' fr ',
}
CLEAN_ADDRESS = {
    'address_line1': '12 Rue de la Paix',
    'country_code': 'FR',
}


@pytest.mark.django_db
def test_preview_does_not_write_or_prompt() -> None:
    """Report changed rows without modifying any address."""
    location = Location.objects.create(
        name='Example',
        address=DIRTY_ADDRESS,
        secondary_address=CLEAN_ADDRESS,
    )
    output = StringIO()

    call_command('normalize_geoaddresses', stdout=output)
    location.refresh_from_db()

    assert 'app.Location.address: 1 to normalize' in output.getvalue()
    assert 'app.Location.secondary_address: 0 to normalize' in output.getvalue()
    assert location.address == DIRTY_ADDRESS
    assert location.secondary_address == CLEAN_ADDRESS


@pytest.mark.django_db
def test_apply_confirms_each_field_and_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Apply only the changes confirmed for each field."""
    location = Location.objects.create(
        name='Example',
        address=DIRTY_ADDRESS,
        secondary_address=DIRTY_ADDRESS,
    )
    other = LocationReadonly.objects.create(
        name='Other',
        address=DIRTY_ADDRESS,
    )
    before_update = location.updated_at
    monkeypatch.setattr('sys.stdin', StringIO('\ny\nn\n'))
    output = StringIO()

    call_command('normalize_geoaddresses', apply=True, stdout=output)
    location.refresh_from_db()
    other.refresh_from_db()

    assert location.address == DIRTY_ADDRESS
    assert location.secondary_address == CLEAN_ADDRESS
    assert other.address == DIRTY_ADDRESS
    assert location.updated_at == before_update
    text = output.getvalue()
    assert text.count('[y/N]') == 3
    assert 'app.Location.secondary_address: 1 normalized' in text


@pytest.mark.django_db
def test_apply_without_input_stops_without_writing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Refuse to apply changes when no confirmation can be read."""
    location = Location.objects.create(name='Example', address=DIRTY_ADDRESS)
    monkeypatch.setattr('sys.stdin', StringIO())

    with pytest.raises(CommandError, match='No confirmation received'):
        call_command('normalize_geoaddresses', apply=True, stdout=StringIO())
    location.refresh_from_db()

    assert location.address == DIRTY_ADDRESS
