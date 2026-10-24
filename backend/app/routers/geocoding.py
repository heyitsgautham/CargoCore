"""
Geocoding endpoints for address search and map integration.
"""
from typing import Any

from fastapi import APIRouter, Query

from app.services import geocoding_service

router = APIRouter(prefix="/api/v1/geocoding", tags=["Geocoding"])


@router.get("/search", response_model=list[dict[str, Any]])
async def search_addresses(
    q: str = Query(..., min_length=3, description="Search query for address"),
    limit: int = Query(5, ge=1, le=10, description="Maximum number of results"),
):
    """
    Search for addresses using OpenStreetMap Nominatim.
    No authentication required - public endpoint.
    """
    results = await geocoding_service.search_address(q, limit)
    return results


@router.get("/reverse", response_model=dict[str, Any])
async def reverse_geocode(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
):
    """
    Reverse geocode coordinates to address.
    No authentication required - public endpoint.
    """
    result = await geocoding_service.reverse_geocode(lat, lon)
    return result
