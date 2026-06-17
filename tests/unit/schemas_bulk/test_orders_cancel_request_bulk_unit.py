import pytest
from pydantic import ValidationError

from app.schemas.orders import CancelOrderRequest


VALID_CASES = [{'reason': 'Cancel due to delay'}, {'reason': 'Client requested change'}, {'reason': 'Wrong address provided'}, {'reason': 'Need to reschedule'}, {'reason': 'Duplicate order created'}, {'reason': 'Service unavailable today'}, {'reason': 'Customer unavailable now'}, {'reason': 'Payment issue encountered'}]
INVALID_CASES = [{'reason': ''}, {'reason': 'a'}, {'reason': 'ab'}, {'reason': '  '}, {'reason': 'x '}, {'reason': ' y'}, {'reason': '\n'}, {'reason': '\t'}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_orders_cancel_request_bulk_unit_valid_bulk(payload) -> None:
    model = CancelOrderRequest(**payload)
    assert isinstance(model, CancelOrderRequest)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_orders_cancel_request_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        CancelOrderRequest(**payload)
