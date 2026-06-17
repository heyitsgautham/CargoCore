import pytest
from pydantic import ValidationError

from app.routers.orders import CustomerRatingRequest


VALID_CASES = [
    {"rating": 1, "feedback": "Minimum accepted"},
    {"rating": 5, "feedback": "Maximum accepted"},
]

INVALID_CASES = [
    {"rating": 0, "feedback": "Below minimum"},
    {"rating": 6, "feedback": "Above maximum"},
]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_customer_rating_request_bulk_valid(payload) -> None:
    model = CustomerRatingRequest(**payload)
    assert isinstance(model, CustomerRatingRequest)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_customer_rating_request_bulk_invalid(payload) -> None:
    with pytest.raises(ValidationError):
        CustomerRatingRequest(**payload)
