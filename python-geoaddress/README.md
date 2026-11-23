# python-geoaddress

Geoaddress is a Python library for address geocoding and reverse geocoding. It provides a unified interface to multiple geocoding providers (Nominatim, Google Maps, Mapbox, etc.) using ProviderKit for provider management.

## Installation

```bash
pip install geoaddress
```

For development:

```bash
pip install -e .
pip install -e ".[dev,lint,quality,security,test]"
```

## Usage

Geoaddress provides a unified interface to multiple geocoding providers through ProviderKit.

### Basic Usage

#### Search Addresses

```python
from geoaddress import addresses_autocomplete

# Search for addresses using available providers
results = addresses_autocomplete("1600 Amphitheatre Parkway, Mountain View, CA")

# Results include addresses from all available providers
for result in results:
    print(f"{result['text']} - {result['latitude']}, {result['longitude']}")
```

#### Reverse Geocoding

```python
from geoaddress import reverse_geocode

# Convert coordinates to address
address = reverse_geocode(37.4224764, -122.0842499)

print(f"Address: {address['text']}")
print(f"City: {address['city']}")
print(f"Country: {address['country']}")
```


### Provider Selection

You can specify which providers to use:

```python
from geoaddress import addresses_autocomplete

# Use only Nominatim provider
results = addresses_autocomplete(
    "Paris, France",
    query_string="nominatim"
)

# Use multiple specific providers
results = addresses_autocomplete(
    "Paris, France",
    query_string="nominatim|photon"
)
```

### Geographic preference

Pass `proximity` as `latitude,longitude` to `search_addresses()` or
`addresses_autocomplete()` to request that providers favor results near a
point:

```python
from geoaddress.helpers import addresses_autocomplete

results = addresses_autocomplete(
    'Rue de la Paix',
    proximity='48.8566,2.3522',
    proximity_radius_km=25,
)
```

Nominatim, Maps.co, LocationIQ and Google use an approximate rectangular
preference area, with a default distance of 100 km from the centre to each
side. `proximity_radius_km` changes that distance and must be positive and
finite. Near a pole or the antimeridian, the rectangle spans all longitudes
to avoid invalid or crossing bounds. The radius does not affect providers
that use a point-based preference instead. With a proximity, invalid
coordinates or an invalid radius for these four providers produce a provider
error in the public API's response.

The rectangle is a preference, not a geographical filter. Provider ranking
and result limits still apply: results outside the rectangle may appear or
may be omitted by the provider. Geoaddress does not sort results by distance
or guarantee their order across providers. HERE's legacy API uses its
existing `prox` parameter; its behavior outside the specified area has not
been verified.

### Provider Configuration

Providers can be configured via environment variables or configuration files:

```python
# Environment variables (provider-specific prefixes)
# NOMINATIM_USER_AGENT=my-app/1.0
# GOOGLE_MAPS_API_KEY=your-api-key
# MAPBOX_ACCESS_TOKEN=your-token

from geoaddress import addresses_autocomplete

# Providers automatically use environment variables
results = addresses_autocomplete("Paris, France")
```

### Loading Providers from Configuration

```python
from geoaddress import get_address_providers, addresses_autocomplete

# Load providers from JSON configuration
providers = get_address_providers(json="providers.json")

# Use specific providers
results = addresses_autocomplete("Paris, France", providers=providers)
```

## Supported Providers

### Free Providers (no API key required)

- **Nominatim**: OpenStreetMap-based geocoding
- **Photon**: Komoot's OpenStreetMap geocoding service

### Paid/API key Providers

- **Google Maps**: Google's geocoding API
- **Mapbox**: Mapbox Geocoding API
- **LocationIQ**: LocationIQ Geocoding API
- **OpenCage**: OpenCage Geocoding API
- **Geocode Earth**: Geocode Earth API
- **Geoapify**: Geoapify Geocoding API
- **Maps.co**: Maps.co Geocoding API
- **HERE**: HERE Geocoding API

## Address Format

All providers return addresses in a standardized format:

```python
{
    "text": "Full formatted address string",
    "reference": "Backend reference ID (place ID)",
    "address_line1": "Street number and name",
    "address_line2": "Building, apartment, floor (optional)",
    "city": "City name",
    "postal_code": "Postal/ZIP code",
    "state": "State/region/province",
    "country": "Country name",
    "country_code": "ISO country code (e.g., FR, US, GB)",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "confidence": 95.0,
    "relevance": 100.0,
    "backend": "Nominatim",
    "backend_name": "nominatim",
    "geoaddress_id": "nominatim-123456"
}
```

### Normalizing and comparing addresses

Use `normalize_address()` to clean data for storage or display. It returns a
new dictionary, cleans whitespace, and uppercases country and subdivision
codes (`country_code`, `state_code`) without changing the casing of other
postal text or the country name. It does not validate or translate codes.

Use `address_key()` to compare structured addresses across providers:

```python
from geoaddress import address_key, normalize_address

address = normalize_address({
    'address_line1': ' 12  Rue de la Paix ',
    'postal_code': '75002',
    'city': 'Paris',
    'country_code': 'fr',
})
other = {
    'address_line1': '12 RUE DE LA PAIX',
    'postal_code': '75002',
    'city': 'PARIS',
    'country_code': 'FR',
    'country': 'France',
}
assert address_key(address) == address_key(other)
```

The key ignores case, whitespace differences, coordinates and provider
metadata, but preserves accents, punctuation, and apartment or building
details. The country name is compared only when no country code is supplied.
This is not fuzzy matching: abbreviations and different field layouts are
not reconciled. A key may be empty or represent an incomplete address; do not
use a matching key alone as proof that two records should be merged.

## CLI Usage

Geoaddress includes a CLI for command-line usage:

```bash
# Search addresses
geoaddress address --query "Paris, France"

# Reverse geocoding
geoaddress reverse --lat 48.8566 --lon 2.3522

# Use specific provider
geoaddress address --query "Paris, France" --backend nominatim
```

## Architecture

Geoaddress uses a provider-based architecture built on ProviderKit:

- Each geocoding service is implemented as a provider inheriting from `GeoaddressProvider`
- `GeoaddressProvider` extends `ProviderBase` from ProviderKit
- Providers are organized in the `providers/` directory
- Common functionality is shared through the base `GeoaddressProvider` class
- Provider discovery and management is handled by ProviderKit

## Environment Variables

### `ENVFILE_PATH`

The `ENVFILE_PATH` environment variable allows you to automatically specify the path to a `.env` file to load when starting services.

**Usage:**

```bash
ENVFILE_PATH=.env.local ./service.py dev install-dev
```

### `ENSURE_VIRTUALENV`

The `ENSURE_VIRTUALENV` environment variable allows you to automatically activate the `.venv` virtual environment if it exists.

**Usage:**

```bash
ENSURE_VIRTUALENV=1 ./service.py quality lint
```

### Provider-Specific Variables

Each provider uses environment variables with specific prefixes:

- `NOMINATIM_USER_AGENT`: User agent for Nominatim requests
- `GOOGLE_MAPS_API_KEY`: Google Maps API key
- `MAPBOX_ACCESS_TOKEN`: Mapbox access token
- `LOCATIONIQ_API_KEY`: LocationIQ API key
- `OPENCAGE_API_KEY`: OpenCage API key
- And more...

## Use Cases

- Address search and autocomplete
- Geocoding addresses to coordinates
- Reverse geocoding coordinates to addresses
- Address validation and normalization
- Multi-provider address lookup with fallback
- Address data standardization across different geocoding services
- Integration with mapping and location-based applications

## Development

Geoaddress uses clicommands for the CLI. See `docs/` for project rules and guidelines.

