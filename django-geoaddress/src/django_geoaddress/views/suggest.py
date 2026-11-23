"""Views for address suggestions."""

from __future__ import annotations

from math import cos, degrees, isfinite, radians
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse, QueryDict
from django.shortcuts import render, redirect
from django.urls import NoReverseMatch, Resolver404, resolve, reverse

from geoaddress import GEOADDRESS_FIELDS_DESCRIPTIONS

from ..models.provider import GeoaddressProviderModel
from ..models.suggest import AddressModel

from . import geoaddressview_enabled_and_login


def _optional_query_value(params: QueryDict, name: str) -> str | None:
    """Treat empty and null-like query values as absent."""
    value = params.get(name)
    if value is None or value.strip().lower() in ('', 'none', 'null'):
        return None
    return value.strip()


def _proximity_parameters(params: QueryDict) -> dict[str, str | float]:
    """Validate and extract proximity parameters from a request.

    Args:
        params: Request query parameters.

    Returns:
        Validated parameters to forward to the provider.

    Raises:
        ValueError: If the coordinates or radius are invalid.
    """
    proximity = _optional_query_value(params, 'proximity')
    radius = _optional_query_value(params, 'proximity_radius_km')
    if proximity is None:
        if radius is not None:
            _proximity_radius(radius, None, None)
        return {}
    try:
        lat, lon = (float(part) for part in proximity.split(','))
    except ValueError as exc:
        raise ValueError('proximity must be latitude,longitude') from exc
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError('proximity coordinates are outside valid ranges')
    result: dict[str, str | float] = {'proximity': proximity}
    if radius is not None:
        result['proximity_radius_km'] = _proximity_radius(radius, lat, lon)
    return result


def _proximity_radius(
    value: str, lat: float | None, lon: float | None,
) -> float:
    """Validate a radius before forwarding it to a provider."""
    try:
        radius = float(value)
    except ValueError as exc:
        raise ValueError('proximity_radius_km must be a number') from exc
    if not isfinite(radius) or radius <= 0:
        raise ValueError('proximity_radius_km must be positive and finite')
    if lat is None or lon is None:
        return radius
    # Check that floating-point rounding does not collapse the bias box.
    lat_offset = degrees(radius / 6371.0088)
    lon_offset = lat_offset / cos(radians(lat))
    if (
        lat - lat_offset == lat + lat_offset
        or lon - lon_offset == lon + lon_offset
    ):
        raise ValueError('proximity_radius_km is too small')
    return radius


@geoaddressview_enabled_and_login("GEOADDRESS_ADDRESSVIEW")
def search_addresses(request: HttpRequest) -> HttpResponse:
    """Search addresses with filters.

    Query parameters:
        - q: Search query string
        - bck: Backend name filter
        - first: Return first result only (1 or 0)
        - format: Response format ('html' or 'json', default: 'html')
        - proximity: Preferred centre as latitude,longitude
        - proximity_radius_km: Approximate preference radius in kilometres

    Returns:
        HTML or JSON response with address suggestions
    """
    format_type = request.GET.get("format", "html")
    query = request.GET.get("q", "").strip()
    backend = request.GET.get("bck", "").strip() or None
    first_param = request.GET.get("first", "")
    first = first_param == "1" if first_param else False
    try:
        proximity_params = _proximity_parameters(request.GET)
    except ValueError as exc:
        return JsonResponse({'error': str(exc)}, status=400)

    # Get addresses using the same method as admin
    addresses = []

    if query:
        kwargs: dict[str, Any] = {'first': first, **proximity_params}
        if backend:
            kwargs["attribute_search"] = {"name": backend}
        addresses = AddressModel.objects.addresses_autocomplete(query=query, **kwargs)
        
    times = AddressModel.objects.get_response_times('addresses_autocomplete')

    if format_type == "json":
        result = []
        for address in addresses:
            address_data = {field: getattr(address, field, None) for field in GEOADDRESS_FIELDS_DESCRIPTIONS}
            address_data["times"] = times.get(address.backend, 0)
            result.append(address_data)
            
        return JsonResponse(
            {"addresses": result, "count": len(result)}, json_dumps_params={"ensure_ascii": False}
        )

    # HTML format (default)
    # Get providers list for backend filter
    providers = GeoaddressProviderModel.objects.all()

    context = {
        "addresses": addresses,  # Pass the queryset directly like admin does
        "query": query,
        "backend": backend,
        "first": first,
        "count": len(addresses),
        "providers": providers,
        "times": times,

    }
    return render(request, "django_geoaddress/address_list.html", context)


@geoaddressview_enabled_and_login("GEOADDRESS_ADDRESSVIEW")
def detail_address(request: HttpRequest, geoaddress_id: str) -> HttpResponse:
    """Detail address view.

    Args:
        request: Django request object
        geoaddress_id: Combined backend_name-latitude:longitude ID (format: name_lat:lon)

    Returns:
        HTML response with address details
    """
    # Use reverse_geocode like the admin does
    qs = AddressModel.objects.reverse_geocode(geoaddress_id=geoaddress_id)
    address = qs.first()
    
    if not address:
        from django.http import Http404
        raise Http404("Address not found")
    
    return render(request, "django_geoaddress/address_detail.html", {"address": address})


def redirect_to_address_list(request: HttpRequest) -> HttpResponse:
    """Redirect to address list view with query parameters.

    Args:
        request: Django request object

    Returns:
        Redirect response to address list or admin autocomplete view
    """
    query_params = request.GET.copy()
    from_url = query_params.pop("from_url", None)

    try:
        if from_url:
            url_resolver = resolve(from_url[0] if isinstance(from_url, list) else from_url)
            if url_resolver.app_name == "admin":
                base_url = reverse("admin:django_geoaddress_addressmodel_address_autocomplete_view")
                if query_params:
                    base_url += f"?{query_params.urlencode()}"
                return redirect(base_url)
    except (Resolver404, NoReverseMatch):
        pass

    base_url = reverse("django_geoaddress:search_addresses")
    if query_params:
        base_url += f"?{query_params.urlencode()}"
    return redirect(base_url)


def redirect_to_address(request: HttpRequest) -> HttpResponse:
    """Redirect to address view.

    Args:
        request: Django request object

    Returns:
        Redirect response to address detail or admin page
    """
    geoaddress_id = request.GET.get("geoaddress_id")
    if not geoaddress_id:
        return redirect(reverse("django_geoaddress:list_addresses"))
    try:
        from_url = request.GET.get("from_url")
        if from_url:
            url_resolver = resolve(from_url)
            if url_resolver.app_name == "admin":
                return redirect(
                    reverse("admin:django_geoaddress_addressmodel_change", args=[geoaddress_id])
                )
    except (Resolver404, NoReverseMatch):
        pass
    return redirect(reverse("django_geoaddress:detail_address", args=[geoaddress_id]))
