from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings

settings = get_settings()

# ── Read-Write Engine (default) ──────────────────────────────────────────────
engine = create_async_engine(
    settings.database_url,
    echo=not settings.is_production,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# ── Read-Only Engine (AI queries) ────────────────────────────────────────────
# PostgreSQL enforces READ ONLY at the transaction level, so even if
# a malicious SQL bypasses application validation, the DB rejects writes.
ro_engine = create_async_engine(
    settings.database_url,
    echo=not settings.is_production,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=5,
    execution_options={
        "postgresql_readonly": True,
        "postgresql_deferrable": True,
    },
    connect_args={
        # 5-second query timeout: prevents runaway SELECT scans
        "server_settings": {"statement_timeout": "5000"},
    },
)

ROAsyncSessionLocal = async_sessionmaker(
    bind=ro_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_ro_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a READ-ONLY async DB session for AI queries."""
    async with ROAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
