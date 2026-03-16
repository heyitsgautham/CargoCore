import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# ── Import models so Alembic detects them ────────────────────────────────────
from app.database import Base  # noqa: F401
import app.models.user  # noqa: F401  registers User + Role with Base.metadata
import app.models.ai_conversation  # noqa: F401  registers AIConversation with Base.metadata
import app.models.escalation  # noqa: F401  registers Escalation with Base.metadata
import app.models.warehouse  # noqa: F401
import app.models.order  # noqa: F401
import app.models.inventory  # noqa: F401
import app.models.labour  # noqa: F401

# Alembic Config object
config = context.config

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata object for autogenerate support
target_metadata = Base.metadata


def get_url() -> str:
    """Return DATABASE_URL from app settings (overrides alembic.ini value)."""
    from app.config import get_settings

    return get_settings().database_url


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no engine, just SQL output)."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using async engine."""
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
