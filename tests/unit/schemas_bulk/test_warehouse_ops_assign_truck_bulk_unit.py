import pytest
from pydantic import ValidationError

from app.schemas.warehouse_operations import AssignTruckRequest


VALID_CASES = [{'vehicle_id': '11111111-1111-1111-1111-111111111111', 'carrier': 'Carrier-0', 'order_id': '22222222-2222-2222-2222-222222222222'}, {'vehicle_id': '11111111-1111-1111-1111-111111111111', 'carrier': 'Carrier-1', 'order_id': None}, {'vehicle_id': '11111111-1111-1111-1111-111111111111', 'carrier': 'Carrier-2', 'order_id': '22222222-2222-2222-2222-222222222222'}, {'vehicle_id': '11111111-1111-1111-1111-111111111111', 'carrier': 'Carrier-3', 'order_id': None}, {'vehicle_id': '11111111-1111-1111-1111-111111111111', 'carrier': 'Carrier-4', 'order_id': '22222222-2222-2222-2222-222222222222'}, {'vehicle_id': '11111111-1111-1111-1111-111111111111', 'carrier': 'Carrier-5', 'order_id': None}, {'vehicle_id': '11111111-1111-1111-1111-111111111111', 'carrier': 'Carrier-6', 'order_id': '22222222-2222-2222-2222-222222222222'}, {'vehicle_id': '11111111-1111-1111-1111-111111111111', 'carrier': 'Carrier-7', 'order_id': None}]
INVALID_CASES = [{'vehicle_id': '11111111-1111-1111-1111-111111111111', 'carrier': ''}, {'vehicle_id': '11111111-1111-1111-1111-111111111111', 'carrier': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'}, {'vehicle_id': 'not-uuid', 'carrier': 'Carrier'}, {'carrier': 'Carrier'}, {'vehicle_id': '11111111-1111-1111-1111-111111111111'}, {'vehicle_id': None, 'carrier': 'Carrier'}, {'vehicle_id': '11111111-1111-1111-1111-111111111111', 'carrier': None}, {'vehicle_id': '11111111-1111-1111-1111-111111111111', 'carrier': 'Carrier', 'order_id': 'not-uuid'}]


@pytest.mark.parametrize("payload", VALID_CASES)
def test_warehouse_ops_assign_truck_bulk_unit_valid_bulk(payload) -> None:
    model = AssignTruckRequest(**payload)
    assert isinstance(model, AssignTruckRequest)


@pytest.mark.parametrize("payload", INVALID_CASES)
def test_warehouse_ops_assign_truck_bulk_unit_invalid_bulk(payload) -> None:
    with pytest.raises(ValidationError):
        AssignTruckRequest(**payload)
