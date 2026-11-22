"""Tests for read-only address previews in the demo administration."""

import pytest
from django.urls import reverse

from tests.app.models import Location, LocationReadonly


@pytest.mark.django_db
@pytest.mark.parametrize(
    ('model', 'changelist'),
    [
        (Location, 'admin:app_location_changelist'),
        (LocationReadonly, 'admin:app_locationreadonly_changelist'),
    ],
)
def test_admin_changelist_shows_readonly_address_preview(
    admin_client,
    model,
    changelist: str,
) -> None:
    """Render structured addresses using the read-only widget."""
    location = model.objects.create(
        name='Example',
        address={
            'address_line1': '12 <Rue> de la Paix',
            'city': 'Paris',
            'postal_code': '75002',
            'country_code': 'FR',
        },
    )

    response = admin_client.get(reverse(changelist))
    html = response.content.decode()

    assert response.status_code == 200
    assert 'geoaddress-autocomplete-readonly-value' in html
    assert '12 &lt;Rue&gt; de la Paix' in html
    assert '75002, Paris' in html
    assert 'https://flagcdn.com/fr.svg' in html
    assert f'data-object-id="{location.pk}"' in html
    assert 'geoaddress_autocomplete.css' in html
    assert 'geoaddress_autocomplete.js' in html


@pytest.mark.django_db
def test_admin_changelist_preserves_text_only_addresses(admin_client) -> None:
    """Keep displaying legacy addresses that only have a text value."""
    Location.objects.create(
        name='Example',
        address={'text': '12 Rue de la Paix'},
    )

    response = admin_client.get(reverse('admin:app_location_changelist'))

    assert '12 Rue de la Paix' in response.content.decode()
