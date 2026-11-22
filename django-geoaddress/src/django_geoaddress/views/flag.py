"""Resolve flag URLs using the configured address processor."""

from django.http import HttpRequest, JsonResponse
from django.views.decorators.http import require_GET

from django_geoaddress.fields import GeoaddressValue


@require_GET
def flag_url(request: HttpRequest) -> JsonResponse:
    """Return the configured flag URL for a country code.

    Args:
        request: Request containing the country code as ``country_code``.

    Returns:
        A JSON response with a URL or null.
    """
    address = GeoaddressValue({'country_code': request.GET.get('country_code')})
    return JsonResponse({'flag_url': address.flag_url})
