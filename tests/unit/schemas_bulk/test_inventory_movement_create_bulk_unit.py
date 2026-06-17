import pytest
from pydantic import ValidationError

from app.schemas.inventory import InventoryMovementCreate


VALID_CASES = [{'item_id': '11111111-1111-1111-1111-111111111111', 'movement_type': 'IN', 'quantity': 1}, {'item_id': '11111111-1111-1111-1111-111111111111', 'movement_type': 'IN', 'quantity': 2}, {'item_id': '11111111-1111-1111-1111-111111111111', 'movement_type': 'IN', 'quantity': 3}, {'item_id': '11111111-1111-1111-1111-111111111111', 'movement_type': 'IN', 'quantity': 5}, {'item_id': '11111111-1111-1111-1111-111111111111', 'movement_type': 'IN', 'quantity': 10}, {'item_id': '11111111-1111-1111-1111-111111111111', 'movement_type': 'IN', 'quantity': 20}, {'item_id': '11111111-1111-1111-1111-111111111111', 'movement_type': 'IN', 'quantity': 50}, {'item_id': '11111111-1111-1111-1111-111111111111', 'movement_type': 'IN', 'quantity': 100}]
INVALID_CASES = [{'item_id': '11111111-1111-1111-1111-111111111111', 'movement_type': 'IN', 'quantity': 0}, {'item_id': '11111111-1111-1111-1111-111111111111', 'movement_type': 'IN', 'quantity': -1}, {'item_id': '11111111-1111-1111-1111-111111111111', 'movement_type': 'IN', 'quantity': -5}, {'item_id': 'not-uuid', 'movement_type': 'IN', 'quantity': 1}, {'item_id': '11111111-1111-1111-1111-111111111111', 'movement_type': 'XXXXXXXXXXXXXXXXXXXXX', 'quantity': 1}, {'movement_type': 'IN', 'quantity': 1}, {'item_id': '11111111-1111-1111-1111-111111111111', 'quantity': 1}, {'item_id': '11111111-1111-1111-1111-111111111111', 'movement_type': 'IN'}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_inventory_movement_create_bulk_unit_valid_bulk(payload) -> None:
    model = InventoryMovementCreate(**payload)
    assert isinstance(model, InventoryMovementCreate)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_inventory_movement_create_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        InventoryMovementCreate(**payload)
