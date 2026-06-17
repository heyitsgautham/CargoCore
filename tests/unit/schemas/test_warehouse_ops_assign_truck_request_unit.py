import pytest
from pydantic import ValidationError

from app.schemas.warehouse_operations import AssignTruckRequest


def test_assign_truck_request_accepts_valid_payload() -> None:
    model = AssignTruckRequest(
        vehicle_id="11111111-1111-1111-1111-111111111111",
        carrier="Carrier-X",
    )
    assert model.carrier == "Carrier-X"


def test_assign_truck_request_rejects_empty_carrier() -> None:
    with pytest.raises(ValidationError):
        AssignTruckRequest(
            vehicle_id="11111111-1111-1111-1111-111111111111",
            carrier="",
        )
