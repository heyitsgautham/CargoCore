import pytest
from pydantic import ValidationError

from app.schemas.auth import ChangePasswordRequest


VALID_CASES = [{'current_password': 'old-pass', 'new_password': 'NNNNNNNN'}, {'current_password': 'old-pass', 'new_password': 'NNNNNNNNN'}, {'current_password': 'old-pass', 'new_password': 'NNNNNNNNNN'}, {'current_password': 'old-pass', 'new_password': 'NNNNNNNNNNN'}, {'current_password': 'old-pass', 'new_password': 'NNNNNNNNNNNN'}, {'current_password': 'old-pass', 'new_password': 'NNNNNNNNNNNNNN'}, {'current_password': 'old-pass', 'new_password': 'NNNNNNNNNNNNNNNN'}, {'current_password': 'old-pass', 'new_password': 'NNNNNNNNNNNNNNNNNNNN'}]
INVALID_CASES = [{'current_password': 'old-pass', 'new_password': ''}, {'current_password': 'old-pass', 'new_password': 'N'}, {'current_password': 'old-pass', 'new_password': 'NN'}, {'current_password': 'old-pass', 'new_password': 'NNN'}, {'current_password': 'old-pass', 'new_password': 'NNNN'}, {'current_password': 'old-pass', 'new_password': 'NNNNN'}, {'current_password': 'old-pass', 'new_password': 'NNNNNN'}, {'current_password': 'old-pass', 'new_password': 'NNNNNNN'}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_auth_change_password_bulk_unit_valid_bulk(payload) -> None:
    model = ChangePasswordRequest(**payload)
    assert isinstance(model, ChangePasswordRequest)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_auth_change_password_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        ChangePasswordRequest(**payload)
