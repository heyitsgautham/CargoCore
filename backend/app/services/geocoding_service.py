"""
Geocoding service using Nominatim (OpenStreetMap) - Free and no API key required.
"""
import time
from typing import Any

import httpx

NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
PHOTON_BASE_URL = "https://photon.komoot.io"
USER_AGENT = "CargoCore/1.0 (Logistics App)"
DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json",
    "Accept-Language": "en",
}
_CACHE_TTL_SECONDS = 180
_search_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_reverse_cache: dict[str, tuple[float, dict[str, Any]]] = {}


def _cache_get(cache: dict[str, tuple[float, Any]], key: str):
    entry = cache.get(key)
    if not entry:
        return None
    saved_at, value = entry
    if time.time() - saved_at > _CACHE_TTL_SECONDS:
        cache.pop(key, None)
        return None
    return value


def _cache_set(cache: dict[str, tuple[float, Any]], key: str, value: Any):
    cache[key] = (time.time(), value)


def _format_photon_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    formatted_results = []
    for item in results:
        geometry = item.get("geometry", {})
        properties = item.get("properties", {})
        coords = geometry.get("coordinates", [0, 0])
        lon = float(coords[0]) if len(coords) > 1 else 0.0
        lat = float(coords[1]) if len(coords) > 1 else 0.0
        parts = [
            properties.get("name"),
            properties.get("street"),
            properties.get("city") or properties.get("district") or properties.get("county"),
            properties.get("state"),
            properties.get("country"),
        ]
        display_name = ", ".join([p for p in parts if p]) or f"{lat:.6f}, {lon:.6f}"
        formatted_results.append(
            {
                "display_name": display_name,
                "lat": lat,
                "lon": lon,
                "address": properties,
                "type": properties.get("osm_value", ""),
                "importance": 0,
            }
        )
    return formatted_results


async def search_address(query: str, limit: int = 5) -> list[dict[str, Any]]:
    """
    Search for addresses using Nominatim geocoding.
    Returns list of address suggestions with coordinates.
    """
    query = (query or "").strip()
    if len(query) < 3:
        return []
    cache_key = f"{query.lower()}|{limit}"
    cached = _cache_get(_search_cache, cache_key)
    if cached is not None:
        return cached
    
    async with httpx.AsyncClient() as client:
        try:
            try:
                response = await client.get(
                    f"{NOMINATIM_BASE_URL}/search",
                    params={
                        "q": query,
                        "format": "json",
                        "limit": limit,
                        "addressdetails": 1,
                        "accept-language": "en",
                    },
                    headers=DEFAULT_HEADERS,
                    timeout=10.0,
                )
                response.raise_for_status()
                results = response.json()
                formatted_results = []
                for result in results:
                    formatted_results.append({
                        "display_name": result.get("display_name", ""),
                        "lat": float(result.get("lat", 0)),
                        "lon": float(result.get("lon", 0)),
                        "address": result.get("address", {}),
                        "type": result.get("type", ""),
                        "importance": result.get("importance", 0),
                    })
                _cache_set(_search_cache, cache_key, formatted_results)
                return formatted_results
            except httpx.HTTPStatusError as e:
                if e.response.status_code != 429:
                    raise

            photon_response = await client.get(
                f"{PHOTON_BASE_URL}/api",
                params={"q": query, "limit": limit, "lang": "en"},
                headers=DEFAULT_HEADERS,
                timeout=10.0,
            )
            photon_response.raise_for_status()
            photon_results = photon_response.json().get("features", [])
            formatted_results = _format_photon_results(photon_results)
            _cache_set(_search_cache, cache_key, formatted_results)
            return formatted_results
        except Exception as e:
            print(f"Geocoding error: {e}")
            return []


async def reverse_geocode(lat: float, lon: float) -> dict[str, Any]:
    """
    Reverse geocode coordinates to address using Nominatim.
    Returns address details for the given coordinates.
    """
    cache_key = f"{lat:.7f}|{lon:.7f}"
    cached = _cache_get(_reverse_cache, cache_key)
    if cached is not None:
        print(f"Returning cached reverse geocode for {lat}, {lon}")
        return cached

    async with httpx.AsyncClient() as client:
        try:
            try:
                print(f"Requesting reverse geocode from Nominatim for {lat}, {lon}")
                response = await client.get(
                    f"{NOMINATIM_BASE_URL}/reverse",
                    params={
                        "lat": lat,
                        "lon": lon,
                        "format": "json",
                        "addressdetails": 1,
                    },
                    headers=DEFAULT_HEADERS,
                    timeout=5.0,
                )
                response.raise_for_status()
                result = response.json()
                print(f"Nominatim response: {result.get('display_name', 'No display_name')}")
                payload = {
                    "display_name": result.get("display_name", f"{lat:.6f}, {lon:.6f}"),
                    "address": result.get("address", {}),
                    "lat": lat,
                    "lon": lon,
                }
                _cache_set(_reverse_cache, cache_key, payload)
                return payload
            except httpx.HTTPStatusError as e:
                if e.response.status_code != 429:
                    raise
                print("Nominatim rate limited, falling back to Photon")

            photon_response = await client.get(
                f"{PHOTON_BASE_URL}/reverse",
                params={"lat": lat, "lon": lon, "lang": "en"},
                headers=DEFAULT_HEADERS,
                timeout=5.0,
            )
            photon_response.raise_for_status()
            features = photon_response.json().get("features", [])
            if features:
                mapped = _format_photon_results([features[0]])[0]
                payload = {
                    "display_name": mapped.get("display_name", f"{lat:.6f}, {lon:.6f}"),
                    "address": mapped.get("address", {}),
                    "lat": lat,
                    "lon": lon,
                }
                print(f"Photon response: {payload.get('display_name')}")
                _cache_set(_reverse_cache, cache_key, payload)
                return payload

            print("No results from Photon, returning coordinates")
            payload = {
                "display_name": f"{lat:.6f}, {lon:.6f}",
                "address": {},
                "lat": lat,
                "lon": lon,
            }
            _cache_set(_reverse_cache, cache_key, payload)
            return payload
        except Exception as e:
            print(f"Reverse geocoding error: {e}")
            return {
                "display_name": f"{lat:.6f}, {lon:.6f}",
                "address": {},
                "lat": lat,
                "lon": lon,
            }
