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

Geoaddress uses qualitybase for development tooling:

```bash
# Quality checks
./service.py quality lint
./service.py quality security
./service.py quality all

# Development tools
./service.py dev venv
./service.py dev install-dev
./service.py dev clean
```

See `docs/` for project rules and guidelines.

