import pytest
from pydantic import ValidationError

from app.schemas.logistics import LogisticsVehicleCreate


def test_logistics_vehicle_create_accepts_valid_payload() -> None:
    model = LogisticsVehicleCreate(code="VH1", vehicle_type="Truck", year=2024)
    assert model.code == "VH1"
    assert model.year == 2024


def test_logistics_vehicle_create_rejects_out_of_range_year() -> None:
    with pytest.raises(ValidationError):
        LogisticsVehicleCreate(code="VH1", vehicle_type="Truck", year=1800)
