from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.services import dispatch_ai_service, orders_service

pytestmark = pytest.mark.asyncio


class _FakeOrderResponse:
    def __init__(self, order_id: str, driver_id: str, vehicle_id: str | None):
        self.order_id = order_id
        self.driver_id = driver_id
        self.vehicle_id = vehicle_id

    def model_dump(self, mode: str = "json") -> dict:
        return {
            "id": str(self.order_id),
            "assigned_driver_id": str(self.driver_id),
            "assigned_vehicle_id": str(self.vehicle_id) if self.vehicle_id else None,
            "status": "ASSIGNED",
        }


async def test_assignment_preview_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    warehouse_id = str(uuid4())

    async def _fake_get_order_assignment_preview(db, warehouse_id_param):
        return {
            "warehouse_id": warehouse_id_param or warehouse_id,
            "warehouse_name": "Main Hub",
            "warehouse_address": "100 Dispatch Street",
            "assignment_type": "selected",
            "message": "Manual assignment ready",
        }

    monkeypatch.setattr(orders_service, "get_order_assignment_preview", _fake_get_order_assignment_preview)

    response = await authorized_client.get(f"/api/v1/orders/assignment-preview?warehouse_id={warehouse_id}")
    body = response.json()

    assert response.status_code == 200
    assert body["assignment_type"] == "selected"

    record_evidence(
        case_id="S2-INT-008",
        endpoint="GET /api/v1/orders/assignment-preview",
        input_data={"query": {"warehouse_id": warehouse_id}},
        expected_output={"status_code": 200, "assignment_type": "selected"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_ai_driver_suggestions_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    async def _fake_suggest_drivers_for_orders(db):
        return [
            {
                "order_id": str(uuid4()),
                "order_tracking_code": "TRK-9901",
                "pickup_addr": "A Street",
                "delivery_addr": "B Street",
                "priority": "HIGH",
                "suggested_driver_id": str(uuid4()),
                "suggested_driver_name": "Driver One",
                "distance_km": 2.7,
                "confidence": 93,
                "reason": "Closest available driver with low workload",
                "ai_powered": True,
            }
        ]

    monkeypatch.setattr(dispatch_ai_service, "suggest_drivers_for_orders", _fake_suggest_drivers_for_orders)

    response = await authorized_client.get("/api/v1/orders/ai-driver-suggestions")
    body = response.json()

    assert response.status_code == 200
    assert body["total"] == 1
    assert body["suggestions"][0]["order_tracking_code"] == "TRK-9901"

    record_evidence(
        case_id="S2-INT-009",
        endpoint="GET /api/v1/orders/ai-driver-suggestions",
        input_data={},
        expected_output={"status_code": 200, "total": 1},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_return_suggestions_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    async def _fake_get_return_trip_suggestions(db):
        return [
            {
                "driver_id": str(uuid4()),
                "driver_name": "Driver Two",
                "pending_order_id": str(uuid4()),
                "pending_tracking_code": "TRK-RET-01",
                "pickup_addr": "Warehouse 5",
                "delivery_addr": "Client Avenue",
                "distance_km": 4.2,
                "priority": "MEDIUM",
                "delivered_minutes_ago": 30,
                "last_delivery_addr": "Zone C",
                "reason": "Driver recently completed nearby drop",
                "ai_powered": True,
            }
        ]

    monkeypatch.setattr(dispatch_ai_service, "get_return_trip_suggestions", _fake_get_return_trip_suggestions)

    response = await authorized_client.get("/api/v1/orders/return-suggestions")
    body = response.json()

    assert response.status_code == 200
    assert body["total"] == 1
    assert body["suggestions"][0]["pending_tracking_code"] == "TRK-RET-01"

    record_evidence(
        case_id="S2-INT-010",
        endpoint="GET /api/v1/orders/return-suggestions",
        input_data={},
        expected_output={"status_code": 200, "total": 1},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_optimize_routes_and_batch_assign_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    order_id = str(uuid4())
    driver_id = str(uuid4())
    vehicle_id = str(uuid4())

    async def _fake_optimize_routes(db, optimize_for, prioritize_urgent):
        return {
            "optimized": True,
            "strategy": optimize_for,
            "prioritize_urgent": prioritize_urgent,
        }

    async def _fake_assign_order(db, order_id_param, assign_data):
        return _FakeOrderResponse(order_id=order_id_param, driver_id=assign_data.driver_id, vehicle_id=assign_data.vehicle_id)

    monkeypatch.setattr(orders_service, "optimize_routes", _fake_optimize_routes)
    monkeypatch.setattr(orders_service, "assign_order", _fake_assign_order)

    optimize_response = await authorized_client.post("/api/v1/orders/optimize-routes?optimize_for=distance&prioritize_urgent=true")
    optimize_body = optimize_response.json()

    batch_payload = {
        "assignments": [
            {
                "order_id": order_id,
                "driver_id": driver_id,
                "vehicle_id": vehicle_id,
            }
        ]
    }
    batch_response = await authorized_client.post("/api/v1/orders/batch-assign", json=batch_payload)
    batch_body = batch_response.json()

    assert optimize_response.status_code == 200
    assert optimize_body["optimized"] is True
    assert batch_response.status_code == 200
    assert isinstance(batch_body, list)
    assert batch_body[0]["status"] == "ASSIGNED"

    record_evidence(
        case_id="S2-INT-011",
        endpoint="POST /api/v1/orders/optimize-routes + POST /api/v1/orders/batch-assign",
        input_data={"optimize": {"optimize_for": "distance", "prioritize_urgent": True}, "batch": batch_payload},
        expected_output={"optimize_status": 200, "batch_status": 200},
        actual_output={
            "optimize_status": optimize_response.status_code,
            "optimize_body": optimize_body,
            "batch_status": batch_response.status_code,
            "batch_body": batch_body,
        },
        status="PASS",
    )
