import pytest
from pydantic import ValidationError

from app.schemas.logistics import LogisticsVehicleCreate


VALID_CASES = [{'code': 'VH0', 'vehicle_type': 'Truck', 'year': 1990, 'mileage': 0}, {'code': 'VH1', 'vehicle_type': 'Truck', 'year': 1995, 'mileage': 1}, {'code': 'VH2', 'vehicle_type': 'Truck', 'year': 2000, 'mileage': 2}, {'code': 'VH3', 'vehicle_type': 'Truck', 'year': 2010, 'mileage': 3}, {'code': 'VH4', 'vehicle_type': 'Truck', 'year': 2020, 'mileage': 4}, {'code': 'VH5', 'vehicle_type': 'Truck', 'year': 2024, 'mileage': 5}, {'code': 'VH6', 'vehicle_type': 'Truck', 'year': 2099, 'mileage': 6}, {'code': 'VH7', 'vehicle_type': 'Truck', 'year': 2100, 'mileage': 7}]
INVALID_CASES = [{'code': 'V', 'vehicle_type': 'Truck'}, {'code': '', 'vehicle_type': 'Truck'}, {'code': 'VH1', 'vehicle_type': 'T'}, {'code': 'VH1', 'vehicle_type': ''}, {'code': 'VH1', 'vehicle_type': 'Truck', 'year': 1989}, {'code': 'VH1', 'vehicle_type': 'Truck', 'year': 2101}, {'code': 'VH1', 'vehicle_type': 'Truck', 'mileage': -1}, {'code': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX', 'vehicle_type': 'Truck'}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_logistics_vehicle_create_bulk_unit_valid_bulk(payload) -> None:
    model = LogisticsVehicleCreate(**payload)
    assert isinstance(model, LogisticsVehicleCreate)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_logistics_vehicle_create_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        LogisticsVehicleCreate(**payload)
