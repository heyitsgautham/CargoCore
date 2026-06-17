import pytest
from pydantic import ValidationError

from app.schemas.orders import OrderItemUpsert


VALID_CASES = [{'sku': 'SKU-0', 'quantity': 1, 'box_count': 0, 'estimated_volume': 0.0}, {'sku': 'SKU-1', 'quantity': 2, 'box_count': 1, 'estimated_volume': 1.0}, {'sku': 'SKU-2', 'quantity': 3, 'box_count': 2, 'estimated_volume': 2.0}, {'sku': 'SKU-3', 'quantity': 4, 'box_count': 3, 'estimated_volume': 3.0}, {'sku': 'SKU-4', 'quantity': 5, 'box_count': 4, 'estimated_volume': 4.0}, {'sku': 'SKU-5', 'quantity': 10, 'box_count': 5, 'estimated_volume': 5.0}, {'sku': 'SKU-6', 'quantity': 20, 'box_count': 6, 'estimated_volume': 6.0}, {'sku': 'SKU-7', 'quantity': 50, 'box_count': 7, 'estimated_volume': 7.0}]
INVALID_CASES = [{'sku': '', 'quantity': 1}, {'sku': 'SKU-1', 'quantity': 0}, {'sku': 'SKU-1', 'quantity': -1}, {'sku': 'SKU-1', 'quantity': 1, 'box_count': -1}, {'sku': 'SKU-1', 'quantity': 1, 'estimated_volume': -0.1}, {'sku': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', 'quantity': 1}, {'sku': 'SKU-1'}, {'quantity': 1}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_orders_item_upsert_bulk_unit_valid_bulk(payload) -> None:
    model = OrderItemUpsert(**payload)
    assert isinstance(model, OrderItemUpsert)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_orders_item_upsert_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        OrderItemUpsert(**payload)
