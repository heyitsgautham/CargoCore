import pytest
from pydantic import ValidationError

from app.schemas.orders import BatchConfirmRequest, DriverSuggestionResponse, ReturnTripResponse


def test_driver_suggestion_response_accepts_valid_payload() -> None:
    model = DriverSuggestionResponse(
        suggestions=[
            {
                "order_id": "order-1",
                "order_tracking_code": "TRK-1",
                "pickup_addr": "Pickup",
                "delivery_addr": "Drop",
                "priority": "HIGH",
                "suggested_driver_id": "driver-1",
                "suggested_driver_name": "Driver One",
                "distance_km": 2.5,
                "confidence": 92,
                "reason": "Closest available driver",
                "ai_powered": True,
            }
        ],
        total=1,
    )

    assert model.total == 1
    assert model.suggestions[0].confidence == 92


def test_return_trip_response_accepts_valid_payload() -> None:
    model = ReturnTripResponse(
        suggestions=[
            {
                "driver_id": "driver-2",
                "driver_name": "Driver Two",
                "pending_order_id": "pending-1",
                "pending_tracking_code": "TRK-RET-1",
                "pickup_addr": "Warehouse",
                "delivery_addr": "Client",
                "distance_km": 4.0,
                "priority": "MEDIUM",
                "delivered_minutes_ago": 25,
                "last_delivery_addr": "Zone A",
                "reason": "Driver is already nearby",
                "ai_powered": True,
            }
        ],
        total=1,
    )

    assert model.total == 1
    assert model.suggestions[0].pending_tracking_code == "TRK-RET-1"


def test_batch_confirm_request_rejects_invalid_uuid_assignments() -> None:
    with pytest.raises(ValidationError):
        BatchConfirmRequest(
            assignments=[
                {
                    "order_id": "not-a-uuid",
                    "driver_id": "not-a-uuid",
                    "vehicle_id": None,
                }
            ]
        )
