"""The reserved Logistics Manager account that the API creates on startup."""

import pytest

from app.config import get_settings
from app.services.admin_bootstrap import (
    BOOTSTRAP_ADMIN_EMAIL,
    ensure_logistic_manager_account,
)

LOGIN = "/api/v1/auth/login"


async def _login(client, password: str) -> int:
    response = await client.post(LOGIN, json={"email": BOOTSTRAP_ADMIN_EMAIL, "password": password})
    return response.status_code


@pytest.fixture()
def bootstrap_password(monkeypatch):
    def set_password(value: str) -> None:
        monkeypatch.setattr(get_settings(), "admin_bootstrap_password", value)

    return set_password


async def test_first_start_uses_the_configured_password(client, db_session, bootstrap_password):
    bootstrap_password("First-Admin-Pass-1")

    await ensure_logistic_manager_account(db_session)
    await db_session.commit()

    assert await _login(client, "First-Admin-Pass-1") == 200


async def test_restart_keeps_a_password_the_manager_changed(client, db_session, bootstrap_password):
    bootstrap_password("First-Admin-Pass-1")
    await ensure_logistic_manager_account(db_session)
    await db_session.commit()

    tokens = (
        await client.post(LOGIN, json={"email": BOOTSTRAP_ADMIN_EMAIL, "password": "First-Admin-Pass-1"})
    ).json()
    changed = await client.post(
        "/api/v1/auth/change-password",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"current_password": "First-Admin-Pass-1", "new_password": "Changed-Admin-Pass-2"},
    )
    assert changed.status_code == 200

    # A second startup runs the bootstrap again.
    await ensure_logistic_manager_account(db_session)
    await db_session.commit()

    assert await _login(client, "Changed-Admin-Pass-2") == 200
    assert await _login(client, "First-Admin-Pass-1") == 401


async def test_without_a_configured_password_no_guessable_password_works(
    client, db_session, bootstrap_password
):
    bootstrap_password("")

    user = await ensure_logistic_manager_account(db_session)
    await db_session.commit()

    assert user.role.name == "LOGISTIC_MANAGER"
    assert await _login(client, "12345678") == 401
