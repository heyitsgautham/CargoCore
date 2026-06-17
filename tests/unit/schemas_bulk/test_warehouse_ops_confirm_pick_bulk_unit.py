import pytest
from pydantic import ValidationError

from app.schemas.warehouse_operations import ConfirmPickItemRequest


VALID_CASES = [{'sku': 'SKU-0', 'quantity_picked': 1, 'location': 'A-0', 'notes': 'ok'}, {'sku': 'SKU-1', 'quantity_picked': 2, 'location': 'A-1', 'notes': 'ok'}, {'sku': 'SKU-2', 'quantity_picked': 3, 'location': 'A-2', 'notes': 'ok'}, {'sku': 'SKU-3', 'quantity_picked': 4, 'location': 'A-3', 'notes': 'ok'}, {'sku': 'SKU-4', 'quantity_picked': 5, 'location': 'A-4', 'notes': 'ok'}, {'sku': 'SKU-5', 'quantity_picked': 10, 'location': 'A-5', 'notes': 'ok'}, {'sku': 'SKU-6', 'quantity_picked': 20, 'location': 'A-6', 'notes': 'ok'}, {'sku': 'SKU-7', 'quantity_picked': 50, 'location': 'A-7', 'notes': 'ok'}]
INVALID_CASES = [{'sku': '', 'quantity_picked': 1}, {'sku': 'SKU', 'quantity_picked': 0}, {'sku': 'SKU', 'quantity_picked': -1}, {'sku': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', 'quantity_picked': 1}, {'sku': 'SKU'}, {'quantity_picked': 1}, {'sku': 'SKU', 'quantity_picked': None}, {}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_warehouse_ops_confirm_pick_bulk_unit_valid_bulk(payload) -> None:
    model = ConfirmPickItemRequest(**payload)
    assert isinstance(model, ConfirmPickItemRequest)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_warehouse_ops_confirm_pick_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        ConfirmPickItemRequest(**payload)
