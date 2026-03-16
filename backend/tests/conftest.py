"""
conftest.py
Shared pytest fixtures for the entire test suite.

Requires a running PostgreSQL instance (or use a local SQLite file for unit tests).
For CI, a separate test database is used: logistics_db_test.
"""
from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import get_settings
from app.database import Base, get_db, get_ro_db
from app.main import app
from app.models import user as _  # noqa: F401 — registers models with Base
from app.models import ai_conversation as _ai_conversation  # noqa: F401
from app.models import escalation as _escalation  # noqa: F401
from app.utils.redis import get_redis

settings = get_settings()

# ── Use a separate test database ──────────────────────────────────────────────
TEST_DATABASE_URL = settings.database_url.replace(
    "/logistics_db", "/logistics_db_test"
)

# NullPool: every acquire() opens a fresh connection on the *current* event loop
# and every release() closes it immediately.  This prevents cross-loop reuse,
# which is the root cause of asyncpg's "another operation is in progress" error
# when pytest-asyncio uses separate session/function event loops.
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestSessionLocal = async_sessionmaker(
    bind=test_engine, class_=AsyncSession, expire_on_commit=False
)


# ── Test DB setup / teardown ──────────────────────────────────────────────────


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    """Create all tables once per test session, drop them afterwards."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Seed roles
        await conn.execute(
            text(
                """
                INSERT INTO roles (name) VALUES
                  ('LOGISTIC_MANAGER'),('WAREHOUSE_MANAGER'),('DISPATCHER'),
                  ('DRIVER'),('LABOURER'),('INDIVIDUAL'),('VENDOR'),('AI_AGENT')
                ON CONFLICT (name) DO NOTHING
                """
            )
        )
    yield
    async with test_engine.begin() as conn:
        # Drop schema with CASCADE to avoid FK-cycle ordering issues during teardown.
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
    await test_engine.dispose()


@pytest_asyncio.fixture()
async def db_session(setup_db) -> AsyncGenerator[AsyncSession, None]:
    """Yield an async session that rolls back after each test."""
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()


# ── Override app dependencies ─────────────────────────────────────────────────


@pytest_asyncio.fixture()
async def redis_mock():
    """Provide an AsyncMock Redis client for unit tests that don't need real Redis."""
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)      # default: no blacklist hit
    mock.setex = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)
    return mock


@pytest_asyncio.fixture()
async def client(db_session: AsyncSession, redis_mock) -> AsyncGenerator[AsyncClient, None]:
    """Return an httpx AsyncClient wired to the test DB and mocked Redis."""

    async def override_get_db():
        yield db_session

    async def override_get_redis():
        yield redis_mock

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_ro_db] = override_get_db  # AI read-only also uses test session
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Convenience fixtures ──────────────────────────────────────────────────────

REGISTER_PAYLOAD = {
    "name": "Test User",
    "email": "test@example.com",
    "phone": "9999999999",
    "password": "StrongPass123",
    "role": "INDIVIDUAL",
}


@pytest_asyncio.fixture()
async def registered_user_tokens(client: AsyncClient) -> dict:
    """Register a user and return the token response dict."""
    response = await client.post("/api/v1/auth/register", json=REGISTER_PAYLOAD)
    assert response.status_code == 201
    return response.json()
