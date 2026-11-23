# django-geoaddress

Django integration for address verification and geocoding. Provides Django fields, widgets, and admin integration for the [geoaddress](https://github.com/octolo/python-geoaddress) library.

## Installation

```bash
pip install django-geoaddress
```

## Features

- **Django Model Fields**: `GeoaddressField` for storing address data in Django models
- **Autocomplete Widget**: Interactive address autocomplete widget with real-time suggestions
- **Admin Integration**: Django admin interface for managing addresses and providers
- **Multiple Providers**: Support for multiple geocoding providers (Google Maps, Mapbox, Nominatim, etc.)
- **Virtual Models**: Uses `django-virtualqueryset` for dynamic provider and address models
- **Address Management**: View, search, and manage addresses through Django admin

## Quick Start

### 1. Add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    # ...
    'django_geoaddress',
]
```

### 2. Include URLs

```python
# urls.py
from django.urls import path, include

urlpatterns = [
    # ...
    path('geoaddress/', include('django_geoaddress.urls')),
]
```

### 3. Use in Models

```python
from django.db import models
from django_geoaddress.fields import GeoaddressField

class MyModel(models.Model):
    address = GeoaddressField()
    # ... other fields
```

### 4. Use in Forms

The `GeoaddressField` automatically uses the `GeoaddressAutocompleteWidget` which provides:
- Real-time address autocomplete
- Address search across multiple providers
- Structured address data storage

### Search API geographic preference

The `suggest/` endpoint accepts optional `proximity` and
`proximity_radius_km` query parameters:

```text
/geoaddress/suggest/?q=Paris&format=json&proximity=48.8566,2.3522&proximity_radius_km=1
```

Coordinates are `latitude,longitude` and the radius is in kilometres. An
empty value, `None` or `null` is treated as omitted. Without a proximity,
no geographic preference is sent and any valid radius is ignored. With a
proximity, an omitted radius defaults to 100 km for providers using a
rectangular preference area. A supplied radius must be positive and finite;
invalid parameters return HTTP 400 with a JSON `error`.
The radius has no effect on providers using a point-based preference.
This is a provider preference, not a filter or a guarantee of ordering;
the existing HERE integration's behavior outside its area is unverified.
The admin autocomplete endpoint and widget do not forward these parameters.

## Address Field

The `GeoaddressField` stores address data as JSON with the following structure:

```python
{
    "text": "Full formatted address string",
    "reference": "Backend reference ID",
    "address_line1": "Street number and name",
    "address_line2": "Building, apartment (optional)",
    "city": "City name",
    "postal_code": "Postal/ZIP code",
    "state": "State/region/province",
    "country": "Country name",
    "country_code": "ISO country code (e.g., FR, US, GB)",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "backend_name": "nominatim",
    "geoaddress_id": "nominatim-123456"
}
```

### Country flag URLs

The built-in FlagCDN processor is used by default. For an address with
`country_code='FR'`, `instance.address.flag_url` returns
`https://flagcdn.com/fr.svg`. The URL is computed on access; it is not stored
in the address JSON and no HTTP request is made by Geoaddress.

To use another CDN or local assets, set `GEOADDRESS_FLAG_URL_PROCESSOR` to the
dotted path of your own function. It receives a trimmed, uppercase two-letter
country code and returns a URL string or `None`. Set
`GEOADDRESS_FLAG_URL_PROCESSOR = None` to disable flag URLs. The property also
returns `None` when the country code is missing or malformed.
The address widget shows the flag on the right of the search field when a URL
is available and updates it when an autocomplete result is selected or the
country code changes. The browser requests the configured image URL.
The demonstration app's Location changelists use the same widget in read-only
mode to preview stored addresses.

### Clean up existing addresses

Preview address normalization without writing to the database:

```bash
python manage.py normalize_geoaddresses
```

Add `--apply` to confirm changes for each field with `y`. Press Enter or
answer `n` to skip that field:

```bash
python manage.py normalize_geoaddresses --apply
```

The command discovers `GeoaddressField` columns on installed, managed models
and reports the number of rows it would change for each field. Use
`--database ALIAS` to select a database other than `default`. It normalizes
postal whitespace and uppercases country and subdivision codes. It does not
lowercase address labels, geocode addresses, or merge records.

Only the confirmed address fields are updated; model `save()` hooks, signals,
and automatic timestamps are not triggered. Each confirmed field is saved in
its own transaction.

## Admin Interface

Django-geoaddress provides admin interfaces for:

- **Address Management**: View and manage addresses with search and filtering
- **Provider Management**: View available geocoding providers and their capabilities
- **Address Autocomplete**: Interactive autocomplete in admin forms

Access the admin at:
- Addresses: `/admin/django_geoaddress/address/`
- Providers: `/admin/django_geoaddress/provider/`

## Supported Providers

The library supports multiple geocoding providers through the `geoaddress` library:

**Free providers** (no API key required):
- Nominatim (OpenStreetMap)
- Photon (Komoot/OSM)

**Paid/API key providers**:
- Google Maps
- Mapbox
- LocationIQ
- OpenCage
- Geocode Earth
- Geoapify
- Maps.co
- HERE

## Configuration

### Provider Configuration

Configure geocoding providers in your Django settings or through environment variables. Each provider may require API keys or specific configuration.

Example:

```python
# settings.py
GEOADDRESS_PROVIDERS = {
    'google_maps': {
        'api_key': 'your-api-key',
    },
    'mapbox': {
        'api_key': 'your-api-key',
    },
}
```

## Requirements

- Django >= 3.2
- Python >= 3.10
- geoaddress (automatically installed as dependency)
- django-virtualqueryset (for virtual models)

## Development

```bash
# Clone the repository
git clone https://github.com/octolo/django-geoaddress.git
cd django-geoaddress

# Install in development mode
pip install -e .
pip install -e ".[dev]"
```

## License

MIT License - see LICENSE file for details.

## Links

- **Homepage**: https://github.com/octolo/django-geoaddress
- **Repository**: https://github.com/octolo/django-geoaddress
- **Issues**: https://github.com/octolo/django-geoaddress/issues
- **geoaddress library**: https://github.com/octolo/python-geoaddress

