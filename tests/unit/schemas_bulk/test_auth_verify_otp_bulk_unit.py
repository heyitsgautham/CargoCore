import pytest
from pydantic import ValidationError

from app.schemas.auth import VerifyOTPRequest


VALID_CASES = [{'email': 'u0@example.com', 'otp': '000000'}, {'email': 'u1@example.com', 'otp': '000001'}, {'email': 'u2@example.com', 'otp': '000002'}, {'email': 'u3@example.com', 'otp': '000003'}, {'email': 'u4@example.com', 'otp': '000004'}, {'email': 'u5@example.com', 'otp': '000005'}, {'email': 'u6@example.com', 'otp': '000006'}, {'email': 'u7@example.com', 'otp': '000007'}]
INVALID_CASES = [{'email': 'u0@example.com', 'otp': ''}, {'email': 'u1@example.com', 'otp': '1'}, {'email': 'u2@example.com', 'otp': '12'}, {'email': 'u3@example.com', 'otp': '123'}, {'email': 'u4@example.com', 'otp': '1234'}, {'email': 'u5@example.com', 'otp': '12345'}, {'email': 'u6@example.com', 'otp': '1234567'}, {'email': 'u7@example.com', 'otp': '12345678'}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_auth_verify_otp_bulk_unit_valid_bulk(payload) -> None:
    model = VerifyOTPRequest(**payload)
    assert isinstance(model, VerifyOTPRequest)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_auth_verify_otp_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        VerifyOTPRequest(**payload)
