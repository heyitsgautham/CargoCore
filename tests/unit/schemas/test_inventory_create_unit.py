import pytest
from pydantic import ValidationError

from app.schemas.inventory import InventoryCreate


def test_inventory_create_accepts_valid_payload() -> None:
    model = InventoryCreate(
        warehouse_id="11111111-1111-1111-1111-111111111111",
        sku="SKU-001",
        name="Bubble Wrap",
        quantity_on_hand=10,
    )
    assert model.sku == "SKU-001"
    assert model.quantity_on_hand == 10


def test_inventory_create_rejects_negative_quantity() -> None:
    with pytest.raises(ValidationError):
        InventoryCreate(
            warehouse_id="11111111-1111-1111-1111-111111111111",
            sku="SKU-001",
            name="Bubble Wrap",
            quantity_on_hand=-1,
        )
