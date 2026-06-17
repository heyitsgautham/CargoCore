from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest
import yaml
from httpx import AsyncClient

from app.services import orders_service

from tests.utils.sample_data import make_order_item, make_order_list_response, make_order_response

OPENAPI_YAML = Path(__file__).resolve().parents[1] / "api-docs" / "openapi.swagger.yaml"


def _load_openapi() -> dict:
    assert OPENAPI_YAML.exists(), "OpenAPI YAML not found. Generate tests/api-docs/openapi.swagger.yaml first."
    with OPENAPI_YAML.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def test_openapi_orders_paths_exist() -> None:
    data = _load_openapi()
    paths = data.get("paths", {})

    assert "/api/v1/orders" in paths
    assert "post" in paths["/api/v1/orders"]
    assert "get" in paths["/api/v1/orders"]
    assert "/api/v1/orders/{order_id}" in paths
    assert "/api/v1/orders/{order_id}/items" in paths
    assert "/api/v1/orders/{order_id}/customer-rating" in paths
    assert "post" in paths["/api/v1/orders/{order_id}/customer-rating"]


def test_openapi_customer_rating_contract_shape() -> None:
    data = _load_openapi()
    paths = data.get("paths", {})

    post_spec = paths["/api/v1/orders/{order_id}/customer-rating"]["post"]
    request_ref = post_spec["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    assert request_ref.endswith("/CustomerRatingRequest")

    schemas = data.get("components", {}).get("schemas", {})
    request_schema = schemas.get("CustomerRatingRequest", {})
    rating_props = request_schema.get("properties", {}).get("rating", {})

    assert rating_props.get("minimum") == 1
    assert rating_props.get("maximum") == 5


def test_openapi_order_response_has_customer_rating_fields() -> None:
    data = _load_openapi()
    schemas = data.get("components", {}).get("schemas", {})
    order_response = schemas.get("OrderResponse", {})
    properties = order_response.get("properties", {})

    assert "customer_rating" in properties
    assert "customer_feedback" in properties


@pytest.mark.asyncio
async def test_order_create_contract(
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

    response = await authorized_client.post("/api/v1/orders", json=payload)
    body = response.json()

    assert response.status_code == 201
    assert set(["id", "tracking_code", "status", "total_amount"]).issubset(body.keys())

    record_evidence(
        case_id="ORD-CON-002",
        endpoint="POST /api/v1/orders",
        input_data=payload,
        expected_output={"status_code": 201, "required_keys": ["id", "tracking_code", "status"]},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


@pytest.mark.asyncio
async def test_order_list_contract(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    async def _fake_list_orders(
        _db,
        _user,
        _page,
        _page_size,
        _status_filter,
        _search=None,
        **_filters,
    ):
        return make_order_list_response(total=1)

    monkeypatch.setattr(orders_service, "list_orders", _fake_list_orders)

    response = await authorized_client.get("/api/v1/orders")
    body = response.json()

    assert response.status_code == 200
    assert set(["items", "total", "page", "page_size"]).issubset(body.keys())
    assert isinstance(body["items"], list)

    record_evidence(
        case_id="ORD-CON-003",
        endpoint="GET /api/v1/orders",
        input_data={"query": {"page": 1, "page_size": 20}},
        expected_output={"status_code": 200, "required_keys": ["items", "total", "page", "page_size"]},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )


@pytest.mark.asyncio
async def test_order_items_contract(
    authorized_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    record_evidence,
) -> None:
    order_id = str(uuid4())

    async def _fake_get_order_items(_db, _order_id):
        return [make_order_item()]

    monkeypatch.setattr(orders_service, "get_order_items", _fake_get_order_items)

    response = await authorized_client.get(f"/api/v1/orders/{order_id}/items")
    body = response.json()

    assert response.status_code == 200
    assert isinstance(body, list)
    assert set(["id", "sku", "quantity"]).issubset(body[0].keys())

    record_evidence(
        case_id="ORD-CON-004",
        endpoint="GET /api/v1/orders/{order_id}/items",
        input_data={"path": {"order_id": order_id}},
        expected_output={"status_code": 200, "required_keys": ["id", "sku", "quantity"]},
        actual_output={"status_code": response.status_code, "body": body},
        status="PASS",
    )
