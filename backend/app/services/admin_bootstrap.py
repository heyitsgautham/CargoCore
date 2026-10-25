"""The reserved Logistics Manager account the API makes sure exists on startup."""

from __future__ import annotations

import secrets

from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User
from app.services.auth_service import _get_role_by_name, _get_user_by_email
from app.utils.hashing import hash_password

BOOTSTRAP_ADMIN_EMAIL = "logisticmanager@gmail.com"
BOOTSTRAP_ADMIN_USERNAME = "logisticmanager"
BOOTSTRAP_ADMIN_NAME = "Logistics Manager"


def bootstrap_admin_password() -> tuple[str, bool]:
    """Return the first password for the reserved admin and whether it was generated.

    ADMIN_BOOTSTRAP_PASSWORD sets it. Without one, the account gets a random
    password, so no deployment ships with a password anyone can look up.
    """
    configured = get_settings().admin_bootstrap_password
    if configured:
        return configured, False
    return secrets.token_urlsafe(16), True


async def ensure_logistic_manager_account(db: AsyncSession) -> User:
    """Create the reserved Logistics Manager admin account, or repair its role.

    The password is set only when the account is created. A restart never
    resets a password the manager has changed.
    """
    role = await _get_role_by_name(db, "LOGISTIC_MANAGER")
    if not role:
        raise RuntimeError("Required role 'LOGISTIC_MANAGER' does not exist")

    user = await _get_user_by_email(db, BOOTSTRAP_ADMIN_EMAIL)

    if user:
        user.role_id = role.id
        user.is_active = True
        if not user.username:
            user.username = BOOTSTRAP_ADMIN_USERNAME
        db.add(user)
        await db.flush()
        await db.refresh(user, attribute_names=["role"])
        logger.info("Bootstrap Logistics Manager account present: {}", BOOTSTRAP_ADMIN_EMAIL)
        return user

    password, generated = bootstrap_admin_password()
    user = User(
        name=BOOTSTRAP_ADMIN_NAME,
        username=BOOTSTRAP_ADMIN_USERNAME,
        email=BOOTSTRAP_ADMIN_EMAIL,
        phone="",
        address="",
        password_hash=hash_password(password),
        role_id=role.id,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user, attribute_names=["role"])
    logger.info("Created bootstrap Logistics Manager account: {}", BOOTSTRAP_ADMIN_EMAIL)
    if generated:
        if get_settings().is_production:
            logger.warning(
                "ADMIN_BOOTSTRAP_PASSWORD is not set, so {} got a random password. "
                "Reset it with the forgot-password flow.",
                BOOTSTRAP_ADMIN_EMAIL,
            )
        else:
            logger.warning(
                "ADMIN_BOOTSTRAP_PASSWORD is not set. Generated password for {}: {}",
                BOOTSTRAP_ADMIN_EMAIL,
                password,
            )
    return user
