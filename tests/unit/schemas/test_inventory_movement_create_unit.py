import pytest
from pydantic import ValidationError

from app.schemas.inventory import InventoryMovementCreate


def test_inventory_movement_create_accepts_positive_quantity() -> None:
    model = InventoryMovementCreate(
        item_id="11111111-1111-1111-1111-111111111111",
        movement_type="IN",
        quantity=5,
    )
    assert model.quantity == 5


def test_inventory_movement_create_rejects_zero_quantity() -> None:
    with pytest.raises(ValidationError):
        InventoryMovementCreate(
            item_id="11111111-1111-1111-1111-111111111111",
            movement_type="IN",
            quantity=0,
        )
