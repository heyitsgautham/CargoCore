import pytest
from pydantic import ValidationError

from app.schemas.orders import CancelOrderRequest


def test_cancel_order_request_accepts_reason() -> None:
    model = CancelOrderRequest(reason="Customer requested cancellation")
    assert model.reason.startswith("Customer")


def test_cancel_order_request_rejects_short_reason() -> None:
    with pytest.raises(ValidationError):
        CancelOrderRequest(reason="no")
