from collections.abc import AsyncGenerator

from loguru import logger
from redis.asyncio import Redis, from_url

from app.config import get_settings

settings = get_settings()

_redis_pool: Redis | None = None
_redis_available: bool = True


async def get_redis_pool() -> Redis | None:
    """Return (or create) the shared async Redis connection pool.
    Returns None if Redis is unavailable so callers can degrade gracefully."""
    global _redis_pool, _redis_available
    # If already confirmed unavailable, skip retry (avoids 1s timeout on every request)
    if not _redis_available:
        return None
    if _redis_pool is None:
        try:
            pool = from_url(settings.redis_url, decode_responses=False, socket_connect_timeout=1)
            # Verify connection is alive before caching
            await pool.ping()
            _redis_pool = pool
            _redis_available = True
        except Exception as e:
            logger.warning(f"Redis unavailable — running without cache/blacklist: {e}")
            _redis_available = False
            return None
    return _redis_pool


async def get_redis() -> AsyncGenerator[Redis | None, None]:
    """FastAPI dependency that yields the Redis client (or None if Redis is down)."""
    redis = await get_redis_pool()
    try:
        yield redis
    finally:
        pass  # Connection pool manages lifecycle; no explicit close per-request

