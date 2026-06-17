from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from httpx import AsyncClient

from app.services import customer_service, vendor_service

OPENAPI_YAML = Path(__file__).resolve().parents[1] / "api-docs" / "openapi.swagger.yaml"


def _load_openapi() -> dict:
    assert OPENAPI_YAML.exists(), "OpenAPI YAML not found. Generate tests/api-docs/openapi.swagger.yaml first."
    with OPENAPI_YAML.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def test_openapi_customer_vendor_paths_exist() -> None:
    data = _load_openapi()
    paths = data.get("paths", {})

    assert "/api/v1/customer/dashboard" in paths
    assert "/api/v1/customer/settings" in paths
    assert "/api/v1/customer/damage-reports" in paths

    assert "/api/v1/vendor/dashboard" in paths
    assert "/api/v1/vendor/settings" in paths
    assert "/api/v1/vendor/support-tickets" in paths


@pytest.mark.asyncio
async def test_customer_settings_contract(
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

    response = await authorized_client.get("/api/v1/customer/settings")
    body = response.json()

    assert response.status_code == 200
    assert "settings" in body
    assert set(["language", "currency", "default_payment", "notification_prefs", "privacy_prefs"]).issubset(
        body["settings"].keys()
    )

    record_evidence(
        case_id="CV-CON-001",
        endpoint="GET /api/v1/customer/settings",
        input_data={"authorization": "Bearer <mocked>"},
        expected_output={"status_code": 200, "required_keys": ["settings"]},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


@pytest.mark.asyncio
async def test_vendor_settings_contract(
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

    response = await authorized_client.get("/api/v1/vendor/settings")
    body = response.json()

    assert response.status_code == 200
    assert "settings" in body
    assert set(["company_name", "tax_id", "contact_person", "phone", "email", "address", "notification_prefs"]).issubset(
        body["settings"].keys()
    )

    record_evidence(
        case_id="CV-CON-002",
        endpoint="GET /api/v1/vendor/settings",
        input_data={"authorization": "Bearer <mocked>"},
        expected_output={"status_code": 200, "required_keys": ["settings"]},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
