"""lib example - Example Python library with src/ structure."""

__version__ = "0.2.3"


GEOADDRESS_FIELDS_ESSENTIALS = {
    "address_line1": {
        "label": "Street number and name",
        "description": "Street number and name",
        "format": "str",
    },
    "address_line2": {
        "label": "Building, apartment, floor (optional)",
        "description": "Building, apartment, floor (optional)",
        "format": "str",
    },
    "address_line3": {
        "label": "Additional address info (optional)",
        "description": "Additional address info (optional)",
        "format": "str",
    },
    "city": {
        "label": "City name",
        "description": "City name",
        "format": "str",
    },
    "postal_code": {
        "label": "Postal/ZIP code",
        "description": "Postal/ZIP code",
        "format": "str",
    },
    "state": {
        "label": "State/region/province",
        "description": "State/region/province",
        "format": "str",
    },
    "country": {
        "label": "Country name",
        "description": "Country name",
        "format": "str",
    },
}

GEOADDRESS_FIELDS_OPTIONALS = {
    "number": {
        "label": "House number",
        "description": "House number",
        "format": "str",
    },
    "street": {
        "label": "Street name",
        "description": "Street name",
        "format": "str",
    },
    "municipality": {
        "label": "Municipality or local administrative unit",
        "description": "Municipality or local administrative unit",
        "format": "str",
    },
    "neighbourhood": {
        "label": "Neighbourhood, quarter, or district",
        "description": "Neighbourhood, quarter, or district",
        "format": "str",
    },
    "region": {
        "label": "Region or administrative area",
        "description": "Region or administrative area",
        "format": "str",
    },
    "county": {
        "label": "County or administrative county",
        "description": "County or administrative county",
        "format": "str",
    },
    "country_code": {
        "label": "ISO country code (e.g., FR, US, GB)",
        "description": "ISO country code (e.g., FR, US, GB)",
        "format": "str",
    },
    "sorting_code": {
        "label": "Sorting code (e.g., CEDEX, BXX, etc.)",
        "description": "Sorting code",
        "format": "str",
    },
}

GEOADDRESS_FIELDS_COORDINATES = {
    "latitude": {
        "label": "Latitude coordinate (float)",
        "description": "Latitude coordinate (float)",
        "format": "float",
    },
    "longitude": {
        "label": "Longitude coordinate (float)",
        "description": "Longitude coordinate (float)",
        "format": "float",
    },
}

GEOADDRESS_FULL_FIELDS = {
    **GEOADDRESS_FIELDS_ESSENTIALS,
    **GEOADDRESS_FIELDS_OPTIONALS,
    **GEOADDRESS_FIELDS_COORDINATES,
}

GEOADDRESS_FIELDS_FORMATS = {
    "city_line": [
        "postal_code", "city"
    ],
    "city_line_sorting": [
        "city_line", "sorting_code"
    ],
    "text_aligned": [
        "address_line1",
        "address_line2",
        "address_line3",
        ["postal_code", "city"],
        ["state", "region"],
        ["country","country_code"],
        ["municipality", "neighbourhood"],
    ],
    "text_2lines": [
        ["address_line1", "address_line2", "address_line3",],
        ["postal_code", "city" "county", "state", "region"],
    ],
    "text_3lines": [
        ["address_line1", "address_line2", "address_line3",],
        ["postal_code", "city" "county", "state", "region"],
        ["country", "country_code"],
    ],
    "text_full": list(GEOADDRESS_FIELDS_ESSENTIALS.keys()),
}

GEOADDRESS_FIELDS_EXTENDED = {
    "text_aligned": {
        "label": "Full formatted address string (aligned)",
        "description": "Full formatted address string (aligned)",
        "format": "text",
    },
    "text_2lines": {
        "label": "Full formatted address string (2 lines)",
        "description": "Full formatted address string (2 lines)",
        "format": "text",
    },
    "text_3lines": {
        "label": "Full formatted address string (3 lines)",
        "description": "Full formatted address string (3 lines)",
        "format": "text",
    },
    "text_full": {
        "label": "Full formatted address string (full)",
        "description": "Full formatted address string (full)",
        "format": "text",
    },
    "address_type": {
        "label": "Address type or place type",
        "description": "Address type or place type",
        "format": "str",
    },
    "osm_id": {
        "label": "OpenStreetMap ID",
        "description": "OpenStreetMap ID",
        "format": "str",
    },
    "osm_type": {
        "label": "OpenStreetMap type",
        "description": "OpenStreetMap type",
        "format": "str",
    },
    "confidence": {
        "label": "Confidence score (0-100%)",
        "description": "Confidence score (0-100%)",
        "format": "float",
    },
    "relevance": {
        "label": "Relevance score (0-100%)",
        "description": "Relevance score (0-100%)",
        "format": "float",
    },
    "backend": {
        "label": "Backend display name",
        "description": "Backend display name",
        "format": "str",
    },
    "backend_name": {
        "label": "Simple backend name (e.g., nominatim)",
        "description": "Simple backend name (e.g., nominatim)",
        "format": "str",
    },
    "geoaddress_id": {
        "label": "Combined backend_name-reference ID",
        "description": "Combined backend_name-reference ID",
        "format": "str",
    },
}

GEOADDRESS_FIELDS_DESCRIPTIONS = {**GEOADDRESS_FULL_FIELDS, **GEOADDRESS_FIELDS_EXTENDED}


GEOADDRESS_FIELDS_SEARCH = {
    "text_full": GEOADDRESS_FIELDS_EXTENDED["text_full"],
    "confidence": GEOADDRESS_FIELDS_EXTENDED["confidence"],
    "relevance": GEOADDRESS_FIELDS_EXTENDED["relevance"],
    "backend": GEOADDRESS_FIELDS_EXTENDED["backend"],
    "backend_name": GEOADDRESS_FIELDS_EXTENDED["backend_name"],
    "geoaddress_id": GEOADDRESS_FIELDS_EXTENDED["geoaddress_id"],
}

__all__ = [
    "GEOADDRESS_FIELDS_DESCRIPTIONS",
    "GEOADDRESS_FIELDS_FORMATS",
    "GEOADDRESS_FIELDS_EXTENDED",
    "GEOADDRESS_FIELDS_SEARCH",
    "GEOADDRESS_FIELDS_ESSENTIALS",
]
