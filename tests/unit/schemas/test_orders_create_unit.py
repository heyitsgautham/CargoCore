import pytest
from pydantic import ValidationError

from app.schemas.orders import OrderCreate


def test_order_create_accepts_minimum_valid_payload() -> None:
    model = OrderCreate(
        order_type="MOVE",
        pickup_addr="123 Pickup Road",
        delivery_addr="456 Delivery Road",
    )
    assert model.order_type == "MOVE"
    assert model.labor_count == 0


def test_order_create_rejects_short_pickup_address() -> None:
    with pytest.raises(ValidationError):
        OrderCreate(
            order_type="MOVE",
            pickup_addr="123",
            delivery_addr="456 Delivery Road",
        )
