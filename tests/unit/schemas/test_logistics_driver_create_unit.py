import pytest
from pydantic import ValidationError

from app.schemas.logistics import LogisticsDriverCreate


def test_logistics_driver_create_accepts_valid_payload() -> None:
    model = LogisticsDriverCreate(name="Driver One", email="driver.one@example.com")
    assert model.name == "Driver One"


def test_logistics_driver_create_rejects_short_name() -> None:
    with pytest.raises(ValidationError):
        LogisticsDriverCreate(name="D", email="driver.one@example.com")
