import pytest
from pydantic import ValidationError

from app.schemas.auth import VerifyOTPRequest


def test_verify_otp_accepts_six_digit_otp() -> None:
    model = VerifyOTPRequest(email="john@example.com", otp="123456")
    assert model.otp == "123456"


def test_verify_otp_rejects_short_otp() -> None:
    with pytest.raises(ValidationError):
        VerifyOTPRequest(email="john@example.com", otp="12345")
