import pytest
from pydantic import ValidationError

from app.schemas.orders import OrderCreate


VALID_CASES = [{'order_type': 'MOVE', 'pickup_addr': '100 Pickup Street', 'delivery_addr': '200 Delivery Street', 'labor_count': 0}, {'order_type': 'MOVE', 'pickup_addr': '101 Pickup Street', 'delivery_addr': '201 Delivery Street', 'labor_count': 1}, {'order_type': 'MOVE', 'pickup_addr': '102 Pickup Street', 'delivery_addr': '202 Delivery Street', 'labor_count': 2}, {'order_type': 'MOVE', 'pickup_addr': '103 Pickup Street', 'delivery_addr': '203 Delivery Street', 'labor_count': 3}, {'order_type': 'MOVE', 'pickup_addr': '104 Pickup Street', 'delivery_addr': '204 Delivery Street', 'labor_count': 4}, {'order_type': 'MOVE', 'pickup_addr': '105 Pickup Street', 'delivery_addr': '205 Delivery Street', 'labor_count': 5}, {'order_type': 'MOVE', 'pickup_addr': '110 Pickup Street', 'delivery_addr': '210 Delivery Street', 'labor_count': 10}, {'order_type': 'MOVE', 'pickup_addr': '120 Pickup Street', 'delivery_addr': '220 Delivery Street', 'labor_count': 20}]
INVALID_CASES = [{'order_type': 'XXXXXXXXXXXXXXXXXXXXX', 'pickup_addr': '12345', 'delivery_addr': '67890'}, {'order_type': 'MOVE', 'pickup_addr': '1234', 'delivery_addr': '67890'}, {'order_type': 'MOVE', 'pickup_addr': '12345', 'delivery_addr': '6789'}, {'order_type': 'MOVE', 'pickup_addr': '12345', 'delivery_addr': '67890', 'labor_count': -1}, {'order_type': 'MOVE', 'pickup_addr': '12345', 'delivery_addr': '67890', 'base_amount': -1}, {'order_type': 'MOVE', 'pickup_addr': '12345', 'delivery_addr': '67890', 'vehicle_amount': -1}, {'order_type': 'MOVE', 'pickup_addr': '12345', 'delivery_addr': '67890', 'tax_amount': -1}, {'order_type': 'MOVE', 'pickup_addr': '12345', 'delivery_addr': '67890', 'total_amount': -1}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_orders_create_bulk_unit_valid_bulk(payload) -> None:
    model = OrderCreate(**payload)
    assert isinstance(model, OrderCreate)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_orders_create_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        OrderCreate(**payload)
