import pytest
from pydantic import ValidationError

from app.schemas.auth import UserRegister


VALID_CASES = [{'name': 'User 0', 'email': 'user0@example.com', 'password': 'StrongPass00X', 'role': 'INDIVIDUAL'}, {'name': 'User 1', 'email': 'user1@example.com', 'password': 'StrongPass01X', 'role': 'VENDOR'}, {'name': 'User 2', 'email': 'user2@example.com', 'password': 'StrongPass02X', 'role': 'INDIVIDUAL'}, {'name': 'User 3', 'email': 'user3@example.com', 'password': 'StrongPass03X', 'role': 'VENDOR'}, {'name': 'User 4', 'email': 'user4@example.com', 'password': 'StrongPass04X', 'role': 'INDIVIDUAL'}, {'name': 'User 5', 'email': 'user5@example.com', 'password': 'StrongPass05X', 'role': 'VENDOR'}, {'name': 'User 6', 'email': 'user6@example.com', 'password': 'StrongPass06X', 'role': 'INDIVIDUAL'}, {'name': 'User 7', 'email': 'user7@example.com', 'password': 'StrongPass07X', 'role': 'VENDOR'}]
INVALID_CASES = [{'name': 'A', 'email': 'u1@example.com', 'password': 'StrongPass123', 'role': 'INDIVIDUAL'}, {'name': 'User', 'email': 'not-an-email', 'password': 'StrongPass123', 'role': 'INDIVIDUAL'}, {'name': 'User', 'email': 'u2@example.com', 'password': 'short', 'role': 'INDIVIDUAL'}, {'name': 'User', 'email': 'u3@example.com', 'password': 'StrongPass123', 'role': 'ADMIN'}, {'name': 'User', 'username': 'ab', 'email': 'u4@example.com', 'password': 'StrongPass123', 'role': 'INDIVIDUAL'}, {'name': 'User', 'email': 'u5@example.com', 'password': 'StrongPass123', 'role': 'INDIVIDUAL', 'business_email': 'bad-email'}, {'name': 'User', 'email': 'u6@example.com', 'password': 'StrongPass123', 'role': 'INDIVIDUAL', 'phone': '111111111111111111111'}, {'name': 'User', 'email': 'u7@example.com', 'password': 'StrongPass123', 'role': 'INDIVIDUAL', 'business_phone': '222222222222222222222'}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_auth_user_register_bulk_unit_valid_bulk(payload) -> None:
    model = UserRegister(**payload)
    assert isinstance(model, UserRegister)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_auth_user_register_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        UserRegister(**payload)
