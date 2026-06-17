import pytest
from pydantic import ValidationError

from app.schemas.auth import UserRegister


def test_user_register_accepts_valid_payload() -> None:
    model = UserRegister(
        name="John Doe",
        email="john@example.com",
        password="StrongPass123",
        role="INDIVIDUAL",
    )
    assert model.name == "John Doe"
    assert model.role == "INDIVIDUAL"


def test_user_register_rejects_short_password() -> None:
    with pytest.raises(ValidationError):
        UserRegister(
            name="John Doe",
            email="john@example.com",
            password="short",
            role="INDIVIDUAL",
        )
