"""
Geocoding utility using OpenStreetMap Nominatim API (free, no API key required).
Converts addresses to lat/lng coordinates.
"""

import asyncio
import logging

import httpx

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
USER_AGENT = "CargoCore-Logistics/1.0"

# Rate limiting: Nominatim requires max 1 request per second
_last_request_time = 0
_rate_limit_lock = asyncio.Lock()


async def _rate_limit():
    """Ensure we don't exceed 1 request per second to Nominatim."""
    global _last_request_time
    async with _rate_limit_lock:
        import time
        current_time = time.time()
        time_since_last = current_time - _last_request_time
        if time_since_last < 1.0:
            await asyncio.sleep(1.0 - time_since_last)
        _last_request_time = time.time()


async def geocode_address(address: str) -> tuple[float, float] | None:
    """
    Convert an address string to (latitude, longitude) coordinates.
    
    Args:
        address: Full address string to geocode
        
    Returns:
        Tuple of (lat, lng) or None if geocoding fails
    """
    if not address or len(address.strip()) < 5:
        return None
    
    await _rate_limit()
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                NOMINATIM_URL,
                params={
                    "q": address,
                    "format": "json",
                    "limit": 1,
                    "addressdetails": 0,
                },
                headers={
                    "User-Agent": USER_AGENT,
                    "Accept-Language": "en",
                }
            )
            
            if response.status_code != 200:
                logger.warning(f"Geocoding API returned {response.status_code} for: {address[:50]}...")
                return None
            
            results = response.json()
            
            if not results:
                logger.info(f"No geocoding results for: {address[:50]}...")
                return None
            
            lat = float(results[0]["lat"])
            lng = float(results[0]["lon"])
            
            logger.info(f"Geocoded '{address[:30]}...' -> ({lat}, {lng})")
            return (lat, lng)
            
    except httpx.TimeoutException:
        logger.warning(f"Geocoding timeout for: {address[:50]}...")
        return None
    except Exception as e:
        logger.error(f"Geocoding error for '{address[:50]}...': {e}")
        return None


def geocode_address_sync(address: str) -> tuple[float, float] | None:
    """
    Synchronous version of geocode_address for use in non-async contexts.
    """
    import time

    import requests
    
    if not address or len(address.strip()) < 5:
        return None
    
    # Simple rate limiting
    time.sleep(1.1)
    
    try:
        response = requests.get(
            NOMINATIM_URL,
            params={
                "q": address,
                "format": "json",
                "limit": 1,
            },
            headers={
                "User-Agent": USER_AGENT,
            },
            timeout=10
        )
        
        if response.status_code != 200:
            return None
        
        results = response.json()
        
        if not results:
            return None
        
        lat = float(results[0]["lat"])
        lng = float(results[0]["lon"])
        return (lat, lng)
        
    except Exception as e:
        logger.error(f"Sync geocoding error: {e}")
        return None
