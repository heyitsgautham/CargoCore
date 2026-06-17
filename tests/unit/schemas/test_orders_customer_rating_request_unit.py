import pytest
from pydantic import ValidationError

from app.routers.orders import CustomerRatingRequest


def test_customer_rating_request_accepts_valid_rating() -> None:
    model = CustomerRatingRequest(rating=5, feedback="Great service")
    assert model.rating == 5


def test_customer_rating_request_rejects_out_of_range_rating() -> None:
    with pytest.raises(ValidationError):
        CustomerRatingRequest(rating=6, feedback="Too high")
