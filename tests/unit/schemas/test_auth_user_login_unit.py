import pytest
from pydantic import ValidationError

from app.schemas.auth import UserLogin


def test_user_login_accepts_valid_payload() -> None:
    model = UserLogin(email="john@example.com", password="pass")
    assert model.email == "john@example.com"


def test_user_login_rejects_short_email_field() -> None:
    with pytest.raises(ValidationError):
        UserLogin(email="ab", password="pass")
