from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.database import get_db
from app.dependencies import get_current_user

from tests.utils.sample_data import make_fake_user

pytestmark = pytest.mark.asyncio

TRACKING_BASE = "/api/v1/tracking"


class _FakeResult:
    def __init__(self, rows=None, first_row=None):
        self._rows = rows or []
        self._first_row = first_row

    def all(self):
        return self._rows

    def first(self):
        return self._first_row


class _FakeDriversDB:
    def __init__(self, rows):
        self._rows = rows

    async def execute(self, _query):
        return _FakeResult(rows=self._rows)


class _FakeOrderDriverDB:
    def __init__(self, order_obj, row):
        self._order_obj = order_obj
        self._row = row

    async def get(self, _model, _order_id):
        return self._order_obj

    async def execute(self, _query):
        return _FakeResult(first_row=self._row)


async def test_tracking_requires_authentication(
    client: AsyncClient,
    record_evidence,
) -> None:
    response = await client.get(f"{TRACKING_BASE}/drivers")
    body = response.json()

    assert response.status_code == 401
    assert body["detail"] == "Not authenticated"

    record_evidence(
        case_id="TRK-INT-001",
        endpoint="GET /api/v1/tracking/drivers",
        input_data={"authorization": None},
        expected_output={"status_code": 401, "detail": "Not authenticated"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_tracking_active_drivers_success(
    client: AsyncClient,
    dependency_override_manager,
    record_evidence,
) -> None:
    now = datetime.now(timezone.utc)
    fake_profile = SimpleNamespace(
        current_location="19.0760,72.8777",
        status="On-Duty",
        updated_at=now,
    )
    fake_user = SimpleNamespace(id=uuid4(), name="Driver One")
    fake_vehicle = SimpleNamespace(id=uuid4(), code="VH-001", updated_at=now)
    fake_db = _FakeDriversDB(rows=[(fake_profile, fake_user, fake_vehicle)])

    async def _override_db():
        yield fake_db

    async def _override_current_user():
        return make_fake_user(role_name="DISPATCHER")

    dependency_override_manager(get_db, _override_db)
    dependency_override_manager(get_current_user, _override_current_user)

    response = await client.get(f"{TRACKING_BASE}/drivers")
    body = response.json()

    assert response.status_code == 200
    assert len(body) == 1
    assert body[0]["driver_name"] == "Driver One"
    assert body[0]["vehicle_code"] == "VH-001"

    record_evidence(
        case_id="TRK-INT-002",
        endpoint="GET /api/v1/tracking/drivers",
        input_data={"authorization": "Bearer <mocked>"},
        expected_output={"status_code": 200, "driver_count": 1},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_tracking_order_driver_success(
    client: AsyncClient,
    dependency_override_manager,
    record_evidence,
) -> None:
    order_id = str(uuid4())
    driver_id = uuid4()
    now = datetime.now(timezone.utc)

    fake_order = SimpleNamespace(assigned_driver_id=driver_id)
    fake_profile = SimpleNamespace(
        current_location="18.5204,73.8567",
        status="In-Transit",
        updated_at=now,
    )
    fake_user = SimpleNamespace(id=driver_id, name="Driver Two")
    fake_vehicle = SimpleNamespace(id=uuid4(), code="VH-002")
    fake_db = _FakeOrderDriverDB(order_obj=fake_order, row=(fake_profile, fake_user, fake_vehicle))

    async def _override_db():
        yield fake_db

    async def _override_current_user():
        return make_fake_user(role_name="INDIVIDUAL")

    dependency_override_manager(get_db, _override_db)
    dependency_override_manager(get_current_user, _override_current_user)

    response = await client.get(f"{TRACKING_BASE}/orders/{order_id}/driver")
    body = response.json()

    assert response.status_code == 200
    assert body["driver_name"] == "Driver Two"
    assert body["status"] == "In-Transit"

    record_evidence(
        case_id="TRK-INT-003",
        endpoint="GET /api/v1/tracking/orders/{order_id}/driver",
        input_data={"path": {"order_id": order_id}},
        expected_output={"status_code": 200, "driver_name": "Driver Two"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_tracking_order_driver_returns_null_when_unassigned(
    client: AsyncClient,
    dependency_override_manager,
    record_evidence,
) -> None:
    order_id = str(uuid4())
    fake_db = _FakeOrderDriverDB(order_obj=None, row=None)

    async def _override_db():
        yield fake_db

    async def _override_current_user():
        return make_fake_user(role_name="INDIVIDUAL")

    dependency_override_manager(get_db, _override_db)
    dependency_override_manager(get_current_user, _override_current_user)

    response = await client.get(f"{TRACKING_BASE}/orders/{order_id}/driver")
    body = response.json()

    assert response.status_code == 200
    assert body is None

    record_evidence(
        case_id="TRK-INT-004",
        endpoint="GET /api/v1/tracking/orders/{order_id}/driver",
        input_data={"path": {"order_id": order_id}},
        expected_output={"status_code": 200, "body": None},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
