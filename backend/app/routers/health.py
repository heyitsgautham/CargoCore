"""Liveness and readiness probes.

/health answers as long as the process serves requests.
/health/ready also checks Postgres and reports Redis, so an orchestrator can hold
traffic until the database is reachable. Redis is optional for the API, which
runs without the token blacklist when it is down, so it never fails readiness.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from loguru import logger
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.redis import get_redis

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness_check(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
    redis: Annotated[Redis | None, Depends(get_redis)],
) -> dict[str, str]:
    checks = {"database": "ok", "redis": "ok"}

    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("Readiness check could not reach the database: {}", exc)
        checks["database"] = "unavailable"

    if redis is None:
        checks["redis"] = "unavailable"
    else:
        try:
            await redis.ping()
        except Exception as exc:
            logger.warning("Readiness check could not reach Redis: {}", exc)
            checks["redis"] = "unavailable"

    ready = checks["database"] == "ok"
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if ready else "unavailable", **checks}
