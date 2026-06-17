from __future__ import annotations

from pathlib import Path

import pytest
from httpx import AsyncClient

from app.services import customer_service, vendor_service

pytestmark = pytest.mark.asyncio

CUSTOMER_BASE = "/api/v1/customer"
VENDOR_BASE = "/api/v1/vendor"


async def test_customer_settings_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    async def _fake_get_customer_settings(_user):
        return {
            "settings": {
                "language": "en",
                "currency": "INR",
                "default_payment": "Full Payment",
                "notification_prefs": {"email": True},
                "privacy_prefs": {"share_tracking": False},
            }
        }

    monkeypatch.setattr(customer_service, "get_customer_settings", _fake_get_customer_settings)

    response = await authorized_client.get(f"{CUSTOMER_BASE}/settings")
    body = response.json()

    assert response.status_code == 200
    assert body["settings"]["language"] == "en"

    record_evidence(
        case_id="CV-INT-001",
        endpoint="GET /api/v1/customer/settings",
        input_data={"authorization": "Bearer <mocked>"},
        expected_output={"status_code": 200, "settings.language": "en"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_customer_damage_report_validation_error_422(
    authorized_client: AsyncClient,
    record_evidence,
) -> None:
    response = await authorized_client.post(f"{CUSTOMER_BASE}/damage-reports", json={})
    body = response.json()

    assert response.status_code == 422
    assert "detail" in body

    record_evidence(
        case_id="CV-INT-002",
        endpoint="POST /api/v1/customer/damage-reports",
        input_data={},
        expected_output={"status_code": 422, "error_key": "detail"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_customer_requires_authentication(
    client: AsyncClient,
    record_evidence,
) -> None:
    response = await client.get(f"{CUSTOMER_BASE}/settings")
    body = response.json()

    assert response.status_code == 401
    assert body["detail"] == "Not authenticated"

    record_evidence(
        case_id="CV-INT-003",
        endpoint="GET /api/v1/customer/settings",
        input_data={"authorization": None},
        expected_output={"status_code": 401, "detail": "Not authenticated"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_vendor_settings_success(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    async def _fake_get_vendor_settings(_user):
        return {
            "settings": {
                "company_name": "Vendor Co",
                "tax_id": "GST-123",
                "contact_person": "Vendor Lead",
                "phone": "9999990000",
                "email": "vendor@example.com",
                "address": "Dock Road",
                "notification_prefs": {"email": True, "sms": False},
            }
        }

    monkeypatch.setattr(vendor_service, "get_vendor_settings", _fake_get_vendor_settings)

    response = await authorized_client.get(f"{VENDOR_BASE}/settings")
    body = response.json()

    assert response.status_code == 200
    assert body["settings"]["email"] == "vendor@example.com"

    record_evidence(
        case_id="CV-INT-004",
        endpoint="GET /api/v1/vendor/settings",
        input_data={"authorization": "Bearer <mocked>"},
        expected_output={"status_code": 200, "settings.email": "vendor@example.com"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_vendor_support_ticket_validation_error_422(
    authorized_client: AsyncClient,
    record_evidence,
) -> None:
    response = await authorized_client.post(f"{VENDOR_BASE}/support-tickets", json={})
    body = response.json()

    assert response.status_code == 422
    assert "detail" in body

    record_evidence(
        case_id="CV-INT-005",
        endpoint="POST /api/v1/vendor/support-tickets",
        input_data={},
        expected_output={"status_code": 422, "error_key": "detail"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


async def test_vendor_requires_authentication(
    client: AsyncClient,
    record_evidence,
) -> None:
    response = await client.get(f"{VENDOR_BASE}/settings")
    body = response.json()

    assert response.status_code == 401
    assert body["detail"] == "Not authenticated"

    record_evidence(
        case_id="CV-INT-006",
        endpoint="GET /api/v1/vendor/settings",
        input_data={"authorization": None},
        expected_output={"status_code": 401, "detail": "Not authenticated"},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
