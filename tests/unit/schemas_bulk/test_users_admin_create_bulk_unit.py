import pytest
from pydantic import ValidationError

from app.schemas.users import UserAdminCreate


VALID_CASES = [{'name': 'Admin 0', 'email': 'admin0@example.com', 'password': 'StrongPass00X', 'role': 'LOGISTIC_MANAGER'}, {'name': 'Admin 1', 'email': 'admin1@example.com', 'password': 'StrongPass01X', 'role': 'LOGISTIC_MANAGER'}, {'name': 'Admin 2', 'email': 'admin2@example.com', 'password': 'StrongPass02X', 'role': 'LOGISTIC_MANAGER'}, {'name': 'Admin 3', 'email': 'admin3@example.com', 'password': 'StrongPass03X', 'role': 'LOGISTIC_MANAGER'}, {'name': 'Admin 4', 'email': 'admin4@example.com', 'password': 'StrongPass04X', 'role': 'LOGISTIC_MANAGER'}, {'name': 'Admin 5', 'email': 'admin5@example.com', 'password': 'StrongPass05X', 'role': 'LOGISTIC_MANAGER'}, {'name': 'Admin 6', 'email': 'admin6@example.com', 'password': 'StrongPass06X', 'role': 'LOGISTIC_MANAGER'}, {'name': 'Admin 7', 'email': 'admin7@example.com', 'password': 'StrongPass07X', 'role': 'LOGISTIC_MANAGER'}]
INVALID_CASES = [{'name': 'A', 'email': 'admin@example.com', 'password': 'StrongPass123', 'role': 'LOGISTIC_MANAGER'}, {'name': 'Admin', 'email': 'bad-email', 'password': 'StrongPass123', 'role': 'LOGISTIC_MANAGER'}, {'name': 'Admin', 'email': 'admin2@example.com', 'password': 'short', 'role': 'LOGISTIC_MANAGER'}, {'name': 'Admin', 'email': 'admin3@example.com', 'password': 'StrongPass123', 'role': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'}, {'name': 'Admin', 'username': 'ab', 'email': 'admin4@example.com', 'password': 'StrongPass123', 'role': 'LOGISTIC_MANAGER'}, {'name': 'Admin', 'email': 'admin5@example.com', 'phone': '111111111111111111111', 'password': 'StrongPass123', 'role': 'LOGISTIC_MANAGER'}, {'name': 'Admin', 'password': 'StrongPass123', 'role': 'LOGISTIC_MANAGER'}, {'name': 'Admin', 'email': 'admin7@example.com', 'password': 'StrongPass123'}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_users_admin_create_bulk_unit_valid_bulk(payload) -> None:
    model = UserAdminCreate(**payload)
    assert isinstance(model, UserAdminCreate)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_users_admin_create_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        UserAdminCreate(**payload)
