from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException
from httpx import AsyncClient

from app.dependencies import get_current_user
from app.services import orders_service

from tests.utils.sample_data import make_fake_user, make_order_item, make_order_list_response, make_order_response

pytestmark = pytest.mark.asyncio

ORDERS_BASE = "/api/v1/orders"


async def test_orders_create_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    payload = {
        "order_type": "MOVE",
        "pickup_addr": "123 Pickup Road",
        "delivery_addr": "456 Delivery Road",
    }

    async def _fake_create_order(_db, _data, _user):
        return make_order_response(status="CREATED")

    monkeypatch.setattr(orders_service, "create_order", _fake_create_order)

    response = await authorized_client.post(ORDERS_BASE, json=payload)
    body = response.json()

    assert response.status_code == 201
    assert body["status"] == "CREATED"

    record_evidence(
        case_id="ORD-INT-001",
        endpoint="POST /api/v1/orders",
        input_data=payload,
        expected_output={"status_code": 201, "status": "CREATED"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_orders_list_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    async def _fake_list_orders(
        _db,
        _user,
        page,
        page_size,
        status_filter,
        search=None,
        **filters,
    ):
        assert page == 1
        assert page_size == 20
        assert status_filter is None
        assert search is None
        assert filters.get("warehouse_substatus") is None
        assert filters.get("order_type") is None
        assert filters.get("pickup_type") is None
        return make_order_list_response(total=1)

    monkeypatch.setattr(orders_service, "list_orders", _fake_list_orders)

    response = await authorized_client.get(ORDERS_BASE)
    body = response.json()

    assert response.status_code == 200
    assert body["total"] == 1
    assert len(body["items"]) == 1

    record_evidence(
        case_id="ORD-INT-002",
        endpoint="GET /api/v1/orders",
        input_data={"query": {"page": 1, "page_size": 20}},
        expected_output={"status_code": 200, "total": 1},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_orders_get_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    order_id = str(uuid4())

    async def _fake_get_order_detail(_db, _order_id, _user):
        data = make_order_response(status="CONFIRMED")
        data["id"] = order_id
        return data

    monkeypatch.setattr(orders_service, "get_order_detail", _fake_get_order_detail)

    response = await authorized_client.get(f"{ORDERS_BASE}/{order_id}")
    body = response.json()

    assert response.status_code == 200
    assert body["id"] == order_id

    record_evidence(
        case_id="ORD-INT-003",
        endpoint="GET /api/v1/orders/{order_id}",
        input_data={"path": {"order_id": order_id}},
        expected_output={"status_code": 200, "id": order_id},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_orders_update_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    order_id = str(uuid4())
    payload = {"pickup_addr": "999 Updated Pickup Road"}

    async def _fake_update_order(_db, _order_id, _user, _data):
        data = make_order_response(status="CONFIRMED")
        data["id"] = order_id
        data["pickup_addr"] = "999 Updated Pickup Road"
        return data

    monkeypatch.setattr(orders_service, "update_order", _fake_update_order)

    response = await authorized_client.put(f"{ORDERS_BASE}/{order_id}", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["pickup_addr"] == "999 Updated Pickup Road"

    record_evidence(
        case_id="ORD-INT-004",
        endpoint="PUT /api/v1/orders/{order_id}",
        input_data={"path": {"order_id": order_id}, "json": payload},
        expected_output={"status_code": 200, "pickup_addr": "999 Updated Pickup Road"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_orders_create_validation_error_422(
    authorized_client: AsyncClient,
    record_evidence,
) -> None:
    payload = {}

    response = await authorized_client.post(ORDERS_BASE, json=payload)
    body = response.json()

    assert response.status_code == 422
    assert "detail" in body

    record_evidence(
        case_id="ORD-INT-005",
        endpoint="POST /api/v1/orders",
        input_data=payload,
        expected_output={"status_code": 422, "error_key": "detail"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_orders_requires_authentication(
    client: AsyncClient,
    record_evidence,
) -> None:
    response = await client.get(ORDERS_BASE)
    body = response.json()

    assert response.status_code == 401
    assert body["detail"] == "Not authenticated"

    record_evidence(
        case_id="ORD-INT-006",
        endpoint="GET /api/v1/orders",
        input_data={"authorization": None},
        expected_output={"status_code": 401, "detail": "Not authenticated"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_orders_get_items_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    order_id = str(uuid4())

    async def _fake_get_order_items(_db, _order_id):
        return [make_order_item()]

    monkeypatch.setattr(orders_service, "get_order_items", _fake_get_order_items)

    response = await authorized_client.get(f"{ORDERS_BASE}/{order_id}/items")
    body = response.json()

    assert response.status_code == 200
    assert len(body) == 1
    assert body[0]["sku"] == "BOX-MEDIUM"

    record_evidence(
        case_id="ORD-INT-007",
        endpoint="GET /api/v1/orders/{order_id}/items",
        input_data={"path": {"order_id": order_id}},
        expected_output={"status_code": 200, "item_count": 1},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_orders_upsert_items_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    order_id = str(uuid4())
    payload = [{"sku": "BOX-MEDIUM", "quantity": 3, "box_count": 1}]

    async def _fake_upsert_order_items(_db, _order_id, _items):
        return [make_order_item()]

    monkeypatch.setattr(orders_service, "upsert_order_items", _fake_upsert_order_items)

    response = await authorized_client.post(f"{ORDERS_BASE}/{order_id}/items", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert len(body) == 1

    record_evidence(
        case_id="ORD-INT-008",
        endpoint="POST /api/v1/orders/{order_id}/items",
        input_data={"path": {"order_id": order_id}, "json": payload},
        expected_output={"status_code": 200, "item_count": 1},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_orders_send_delivery_otp_success_for_driver(
    client: AsyncClient,
    dependency_override_manager,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    order_id = str(uuid4())
    payload = {"force_resend": False}

    driver_user = make_fake_user(role_name="DRIVER")

    async def _override_current_user():
        return driver_user

    dependency_override_manager(get_current_user, _override_current_user)

    async def _fake_send_delivery_otp(_db, _order_id, _user, force_resend=False):
        return {
            "message": "Delivery OTP sent",
            "email": "customer@example.com",
            "sent_at": "2026-04-03T00:00:00+00:00",
            "debug_otp": "123456",
        }

    monkeypatch.setattr(orders_service, "send_delivery_otp", _fake_send_delivery_otp)

    response = await client.post(f"{ORDERS_BASE}/{order_id}/delivery-otp/send", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["message"] == "Delivery OTP sent"

    record_evidence(
        case_id="ORD-INT-009",
        endpoint="POST /api/v1/orders/{order_id}/delivery-otp/send",
        input_data={"path": {"order_id": order_id}, "json": payload},
        expected_output={"status_code": 200, "message": "Delivery OTP sent"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_orders_track_unknown_returns_404(
    client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    tracking_code = "UNKNOWN-TRACKING"

    async def _fake_track_order(_db, _tracking_code):
        raise HTTPException(status_code=404, detail="Tracking code not found")

    monkeypatch.setattr(orders_service, "track_order", _fake_track_order)

    response = await client.get(f"{ORDERS_BASE}/track/{tracking_code}")
    body = response.json()

    assert response.status_code == 404
    assert body["detail"] == "Tracking code not found"

    record_evidence(
        case_id="ORD-INT-010",
        endpoint="GET /api/v1/orders/track/{tracking_code}",
        input_data={"path": {"tracking_code": tracking_code}},
        expected_output={"status_code": 404, "detail": "Tracking code not found"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_orders_customer_rating_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    order_id = str(uuid4())
    payload = {"rating": 5, "feedback": "Great service"}

    async def _fake_submit_customer_rating(_db, _order_id, _user, *, rating, feedback=None):
        assert str(_order_id) == order_id
        assert rating == 5
        assert feedback == "Great service"
        data = make_order_response(status="DELIVERED")
        data["id"] = order_id
        data["customer_rating"] = rating
        data["customer_feedback"] = feedback
        return data

    monkeypatch.setattr(orders_service, "submit_customer_rating", _fake_submit_customer_rating)

    response = await authorized_client.post(f"{ORDERS_BASE}/{order_id}/customer-rating", json=payload)
    body = response.json()

    assert response.status_code == 200
    assert body["customer_rating"] == 5
    assert body["customer_feedback"] == "Great service"

    record_evidence(
        case_id="ORD-INT-011",
        endpoint="POST /api/v1/orders/{order_id}/customer-rating",
        input_data={"path": {"order_id": order_id}, "json": payload},
        expected_output={"status_code": 200, "customer_rating": 5},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_orders_customer_rating_validation_error_422(
    authorized_client: AsyncClient,
    record_evidence,
) -> None:
    order_id = str(uuid4())
    payload = {"rating": 6, "feedback": "Invalid rating"}

    response = await authorized_client.post(f"{ORDERS_BASE}/{order_id}/customer-rating", json=payload)
    body = response.json()

    assert response.status_code == 422
    assert "detail" in body

    record_evidence(
        case_id="ORD-INT-012",
        endpoint="POST /api/v1/orders/{order_id}/customer-rating",
        input_data={"path": {"order_id": order_id}, "json": payload},
        expected_output={"status_code": 422, "error_key": "detail"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_orders_customer_rating_requires_authentication(
    client: AsyncClient,
    record_evidence,
) -> None:
    order_id = str(uuid4())
    payload = {"rating": 5, "feedback": "Great service"}

    response = await client.post(f"{ORDERS_BASE}/{order_id}/customer-rating", json=payload)
    body = response.json()

    assert response.status_code == 401
    assert body["detail"] == "Not authenticated"

    record_evidence(
        case_id="ORD-INT-013",
        endpoint="POST /api/v1/orders/{order_id}/customer-rating",
        input_data={"path": {"order_id": order_id}, "json": payload, "authorization": None},
        expected_output={"status_code": 401, "detail": "Not authenticated"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
