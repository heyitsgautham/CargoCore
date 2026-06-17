import pytest
from pydantic import ValidationError

from app.schemas.inventory import RestockRequestStatusUpdate


VALID_CASES = [{'status': 'APPROVED'}, {'status': 'REJECTED'}, {'status': 'APPROVED', 'manager_notes': 'ok'}, {'status': 'REJECTED', 'manager_notes': 'no'}, {'status': 'APPROVED', 'funding_source': 'APP_REVENUE'}, {'status': 'REJECTED', 'funding_source': 'OFFLINE_CAPITAL'}, {'status': 'APPROVED', 'funding_source': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'}, {'status': 'REJECTED', 'funding_source': 'BUDGET_2026'}]
INVALID_CASES = [{'status': 'PENDING'}, {'status': 'approved'}, {'status': 'REJECT'}, {'status': ''}, {'status': 'APPROVED '}, {'status': ' REJECTED'}, {'status': 'APPROVE'}, {'status': 'APPROVED', 'funding_source': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_inventory_restock_status_bulk_unit_valid_bulk(payload) -> None:
    model = RestockRequestStatusUpdate(**payload)
    assert isinstance(model, RestockRequestStatusUpdate)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_inventory_restock_status_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        RestockRequestStatusUpdate(**payload)
