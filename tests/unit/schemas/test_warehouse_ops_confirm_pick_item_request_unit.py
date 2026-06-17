import pytest
from pydantic import ValidationError

from app.schemas.warehouse_operations import ConfirmPickItemRequest


def test_confirm_pick_item_request_accepts_valid_payload() -> None:
    model = ConfirmPickItemRequest(sku="SKU-001", quantity_picked=1)
    assert model.sku == "SKU-001"


def test_confirm_pick_item_request_rejects_zero_quantity() -> None:
    with pytest.raises(ValidationError):
        ConfirmPickItemRequest(sku="SKU-001", quantity_picked=0)
