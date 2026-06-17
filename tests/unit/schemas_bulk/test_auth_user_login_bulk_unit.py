import pytest
from pydantic import ValidationError

from app.schemas.auth import UserLogin


VALID_CASES = [{'email': 'abc', 'password': 'pass1234'}, {'email': 'john@example.com', 'password': 'pass1234'}, {'email': 'user.name', 'password': 'pass1234'}, {'email': 'customer_01', 'password': 'pass1234'}, {'email': 'login-id-123', 'password': 'pass1234'}, {'email': 'employee@example', 'password': 'pass1234'}, {'email': 'person@x', 'password': 'pass1234'}, {'email': 'account01', 'password': 'pass1234'}]
INVALID_CASES = [{'email': '', 'password': 'pass1234'}, {'email': 'a', 'password': 'pass1234'}, {'email': 'ab', 'password': 'pass1234'}, {'email': 'ab', 'password': ''}, {'email': ''}, {'password': 'pass1234'}, {}, {'email': 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa', 'password': 'pass1234'}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_auth_user_login_bulk_unit_valid_bulk(payload) -> None:
    model = UserLogin(**payload)
    assert isinstance(model, UserLogin)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_auth_user_login_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        UserLogin(**payload)
