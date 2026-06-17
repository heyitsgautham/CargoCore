import pytest
from pydantic import ValidationError

from app.schemas.users import UserAdminCreate


def test_user_admin_create_accepts_valid_payload() -> None:
    model = UserAdminCreate(
        name="Admin User",
        email="admin@example.com",
        password="StrongPass123",
        role="LOGISTIC_MANAGER",
    )
    assert model.role == "LOGISTIC_MANAGER"


def test_user_admin_create_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        UserAdminCreate(
            name="Admin User",
            email="admin@example.com",
            password="short",
            role="LOGISTIC_MANAGER",
        )
