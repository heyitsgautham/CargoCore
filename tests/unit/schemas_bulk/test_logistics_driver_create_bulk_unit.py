import pytest
from pydantic import ValidationError

from app.schemas.logistics import LogisticsDriverCreate


VALID_CASES = [{'name': 'Driver 0', 'email': 'driver0@example.com'}, {'name': 'Driver 1', 'email': 'driver1@example.com'}, {'name': 'Driver 2', 'email': 'driver2@example.com'}, {'name': 'Driver 3', 'email': 'driver3@example.com'}, {'name': 'Driver 4', 'email': 'driver4@example.com'}, {'name': 'Driver 5', 'email': 'driver5@example.com'}, {'name': 'Driver 6', 'email': 'driver6@example.com'}, {'name': 'Driver 7', 'email': 'driver7@example.com'}]
INVALID_CASES = [{'name': 'D', 'email': 'driver@example.com'}, {'name': '', 'email': 'driver@example.com'}, {'name': 'Driver', 'email': 'abcd'}, {'name': 'Driver', 'email': ''}, {'name': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', 'email': 'driver@example.com'}, {'name': 'Driver'}, {'email': 'driver@example.com'}, {}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_logistics_driver_create_bulk_unit_valid_bulk(payload) -> None:
    model = LogisticsDriverCreate(**payload)
    assert isinstance(model, LogisticsDriverCreate)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_logistics_driver_create_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        LogisticsDriverCreate(**payload)
