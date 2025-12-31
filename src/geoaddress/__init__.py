"""lib example - Example Python library with src/ structure."""

__version__ = "0.1.0"


GEOADDRESS_FIELDS_ESSENTIALS = {
    "address_line1": "Street number and name",
    "address_line2": "Building, apartment, floor (optional)",
    "address_line3": "Additional address info (optional)",
    "city": "City name",
    "postal_code": "Postal/ZIP code",
    "state": "State/region/province",
    "region": "Region or administrative area",
    "county": "County or administrative county",
    "country": "Country name",
    "country_code": "ISO country code (e.g., FR, US, GB)",
    "municipality": "Municipality or local administrative unit",
    "neighbourhood": "Neighbourhood, quarter, or district",
    "latitude": "Latitude coordinate (float)",
    "longitude": "Longitude coordinate (float)",
}

GEOADDRESS_FIELDS_EXTENDED = {
    "text": "Full formatted address string",
    "reference": "Backend reference ID (place ID)",
    "address_type": "Address type or place type",
    "osm_id": "OpenStreetMap ID",
    "osm_type": "OpenStreetMap type",
    "confidence": "Confidence score (0-100%)",
    "relevance": "Relevance score (0-100%)",
    "backend": "Backend display name",
    "backend_name": "Simple backend name (e.g., nominatim)",
    "geoaddress_id": "Combined backend_name-reference ID",
}

GEOADDRESS_FIELDS_DESCRIPTIONS = {**GEOADDRESS_FIELDS_ESSENTIALS, **GEOADDRESS_FIELDS_EXTENDED}


__all__ = [
    "GEOADDRESS_FIELDS_DESCRIPTIONS",
]
