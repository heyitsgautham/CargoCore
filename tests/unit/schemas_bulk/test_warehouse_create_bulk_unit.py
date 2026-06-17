import pytest
from pydantic import ValidationError

from app.schemas.warehouse import WarehouseCreate


VALID_CASES = [{'name': 'WH-0', 'address': '100 Warehouse Street', 'capacity_limit': 0}, {'name': 'WH-1', 'address': '101 Warehouse Street', 'capacity_limit': 10}, {'name': 'WH-2', 'address': '102 Warehouse Street', 'capacity_limit': 20}, {'name': 'WH-3', 'address': '103 Warehouse Street', 'capacity_limit': 30}, {'name': 'WH-4', 'address': '104 Warehouse Street', 'capacity_limit': 40}, {'name': 'WH-5', 'address': '105 Warehouse Street', 'capacity_limit': 50}, {'name': 'WH-6', 'address': '106 Warehouse Street', 'capacity_limit': 60}, {'name': 'WH-7', 'address': '107 Warehouse Street', 'capacity_limit': 70}]
INVALID_CASES = [{'name': 'W', 'address': '12345'}, {'name': '', 'address': '12345'}, {'name': 'WH', 'address': '1234'}, {'name': 'WH', 'address': ''}, {'name': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', 'address': '12345'}, {'name': 'WH', 'address': '12345', 'capacity_limit': -1}, {'name': 'WH', 'address': '12345', 'manager_id': 'not-uuid'}, {'address': '12345'}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_warehouse_create_bulk_unit_valid_bulk(payload) -> None:
    model = WarehouseCreate(**payload)
    assert isinstance(model, WarehouseCreate)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_warehouse_create_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        WarehouseCreate(**payload)
