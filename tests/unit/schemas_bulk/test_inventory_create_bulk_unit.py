import pytest
from pydantic import ValidationError

from app.schemas.inventory import InventoryCreate


VALID_CASES = [{'warehouse_id': '11111111-1111-1111-1111-111111111111', 'sku': 'SKU-000', 'name': 'Item 0', 'quantity_on_hand': 0, 'safety_stock': 0, 'cost_price': 0.0, 'selling_price': 1.0}, {'warehouse_id': '11111111-1111-1111-1111-111111111111', 'sku': 'SKU-001', 'name': 'Item 1', 'quantity_on_hand': 1, 'safety_stock': 1, 'cost_price': 1.0, 'selling_price': 2.0}, {'warehouse_id': '11111111-1111-1111-1111-111111111111', 'sku': 'SKU-002', 'name': 'Item 2', 'quantity_on_hand': 2, 'safety_stock': 2, 'cost_price': 2.0, 'selling_price': 3.0}, {'warehouse_id': '11111111-1111-1111-1111-111111111111', 'sku': 'SKU-003', 'name': 'Item 3', 'quantity_on_hand': 5, 'safety_stock': 3, 'cost_price': 3.0, 'selling_price': 4.0}, {'warehouse_id': '11111111-1111-1111-1111-111111111111', 'sku': 'SKU-004', 'name': 'Item 4', 'quantity_on_hand': 10, 'safety_stock': 4, 'cost_price': 4.0, 'selling_price': 5.0}, {'warehouse_id': '11111111-1111-1111-1111-111111111111', 'sku': 'SKU-005', 'name': 'Item 5', 'quantity_on_hand': 20, 'safety_stock': 5, 'cost_price': 5.0, 'selling_price': 6.0}, {'warehouse_id': '11111111-1111-1111-1111-111111111111', 'sku': 'SKU-006', 'name': 'Item 6', 'quantity_on_hand': 50, 'safety_stock': 6, 'cost_price': 6.0, 'selling_price': 7.0}, {'warehouse_id': '11111111-1111-1111-1111-111111111111', 'sku': 'SKU-007', 'name': 'Item 7', 'quantity_on_hand': 100, 'safety_stock': 7, 'cost_price': 7.0, 'selling_price': 8.0}]
INVALID_CASES = [{'warehouse_id': '11111111-1111-1111-1111-111111111111', 'sku': '', 'name': 'Item', 'quantity_on_hand': 1}, {'warehouse_id': '11111111-1111-1111-1111-111111111111', 'sku': 'SKU', 'name': '', 'quantity_on_hand': 1}, {'warehouse_id': '11111111-1111-1111-1111-111111111111', 'sku': 'SKU', 'name': 'Item', 'quantity_on_hand': -1}, {'warehouse_id': '11111111-1111-1111-1111-111111111111', 'sku': 'SKU', 'name': 'Item', 'safety_stock': -1}, {'warehouse_id': '11111111-1111-1111-1111-111111111111', 'sku': 'SKU', 'name': 'Item', 'cost_price': -0.1}, {'warehouse_id': '11111111-1111-1111-1111-111111111111', 'sku': 'SKU', 'name': 'Item', 'selling_price': -0.1}, {'warehouse_id': 'not-uuid', 'sku': 'SKU', 'name': 'Item', 'quantity_on_hand': 1}, {'warehouse_id': '11111111-1111-1111-1111-111111111111', 'sku': 'SKU', 'name': 'Item', 'unit': ''}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_inventory_create_bulk_unit_valid_bulk(payload) -> None:
    model = InventoryCreate(**payload)
    assert isinstance(model, InventoryCreate)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_inventory_create_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        InventoryCreate(**payload)
