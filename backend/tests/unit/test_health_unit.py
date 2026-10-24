from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_db
from app.main import app
from app.utils.redis import get_redis


@pytest.fixture()
def override():
    def _set(db, redis):
        async def _db():
            yield db

        async def _redis():
            yield redis

        app.dependency_overrides[get_db] = _db
        app.dependency_overrides[get_redis] = _redis

    yield _set
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_redis, None)


async def _get(path: str):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(path)


async def test_liveness_needs_no_dependencies() -> None:
    response = await _get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_ready_when_database_and_redis_answer(override) -> None:
    db, redis = AsyncMock(), AsyncMock()
    override(db, redis)

    response = await _get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok", "redis": "ok"}
    db.execute.assert_awaited_once()
    redis.ping.assert_awaited_once()


async def test_not_ready_when_the_database_query_fails(override) -> None:
    db = AsyncMock()
    db.execute.side_effect = ConnectionRefusedError("db down")
    override(db, AsyncMock())

    response = await _get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable", "database": "unavailable", "redis": "ok"}


@pytest.mark.parametrize("redis_down", ["missing", "ping_fails"])
async def test_redis_outage_is_reported_but_does_not_fail_readiness(override, redis_down) -> None:
    redis = None
    if redis_down == "ping_fails":
        redis = AsyncMock()
        redis.ping.side_effect = TimeoutError("redis timeout")
    override(AsyncMock(), redis)

    response = await _get("/health/ready")

    assert response.status_code == 200
    assert response.json()["redis"] == "unavailable"
    assert response.json()["database"] == "ok"
