import pytest
from pydantic import ValidationError

from app.schemas.users import AssignRoleRequest


def test_assign_role_request_accepts_valid_role() -> None:
    model = AssignRoleRequest(role="WAREHOUSE_MANAGER")
    assert model.role == "WAREHOUSE_MANAGER"


def test_assign_role_request_rejects_too_long_role() -> None:
    with pytest.raises(ValidationError):
        AssignRoleRequest(role="R" * 51)
