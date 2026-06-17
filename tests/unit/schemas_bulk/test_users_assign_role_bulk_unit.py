import pytest
from pydantic import ValidationError

from app.schemas.users import AssignRoleRequest


VALID_CASES = [{'role': 'LOGISTIC_MANAGER'}, {'role': 'WAREHOUSE_MANAGER'}, {'role': 'DISPATCHER'}, {'role': 'DRIVER'}, {'role': 'LABOURER'}, {'role': 'INDIVIDUAL'}, {'role': 'VENDOR'}, {'role': 'AI_AGENT'}]
INVALID_CASES = [{'role': 'RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR'}, {'role': 'RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR'}, {'role': 'RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR'}, {'role': 'RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR'}, {'role': 'RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR'}, {'role': 'RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR'}, {'role': 'RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR'}, {'role': 'RRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRR'}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_users_assign_role_bulk_unit_valid_bulk(payload) -> None:
    model = AssignRoleRequest(**payload)
    assert isinstance(model, AssignRoleRequest)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_users_assign_role_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        AssignRoleRequest(**payload)
