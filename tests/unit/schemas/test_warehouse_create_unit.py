import pytest
from pydantic import ValidationError

from app.schemas.warehouse import WarehouseCreate


def test_warehouse_create_accepts_valid_payload() -> None:
    model = WarehouseCreate(name="WH-01", address="123 Warehouse Street")
    assert model.name == "WH-01"


def test_warehouse_create_rejects_short_address() -> None:
    with pytest.raises(ValidationError):
        WarehouseCreate(name="WH-01", address="abc")
