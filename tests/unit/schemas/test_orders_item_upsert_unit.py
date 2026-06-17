import pytest
from pydantic import ValidationError

from app.schemas.orders import OrderItemUpsert


def test_order_item_upsert_accepts_valid_payload() -> None:
    model = OrderItemUpsert(sku="BOX-MEDIUM", quantity=2)
    assert model.sku == "BOX-MEDIUM"
    assert model.quantity == 2


def test_order_item_upsert_rejects_non_positive_quantity() -> None:
    with pytest.raises(ValidationError):
        OrderItemUpsert(sku="BOX-MEDIUM", quantity=0)
