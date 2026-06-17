import pytest
from pydantic import ValidationError

from app.schemas.auth import ChangePasswordRequest


def test_change_password_accepts_valid_payload() -> None:
    model = ChangePasswordRequest(current_password="oldpass", new_password="newpass123")
    assert model.new_password == "newpass123"


def test_change_password_rejects_short_new_password() -> None:
    with pytest.raises(ValidationError):
        ChangePasswordRequest(current_password="oldpass", new_password="short")
