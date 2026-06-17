from __future__ import annotations

from pathlib import Path

import yaml

OPENAPI_YAML = Path(__file__).resolve().parents[1] / "api-docs" / "openapi.swagger.yaml"
_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def _load_openapi() -> dict:
    assert OPENAPI_YAML.exists(), "OpenAPI YAML not found. Generate tests/api-docs/openapi.swagger.yaml first."
    with OPENAPI_YAML.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def _iter_operations(openapi_data: dict):
    for path, path_item in openapi_data.get("paths", {}).items():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            method_name = str(method).lower()
            if method_name not in _METHODS:
                continue
            if not isinstance(operation, dict):
                continue
            yield str(path), method_name, operation


def test_openapi_has_user_story_mapping_blocks() -> None:
    data = _load_openapi()

    user_stories = data.get("x-user-stories")
    api_mapping = data.get("x-api-mapping")

    assert isinstance(user_stories, list) and user_stories, "x-user-stories must exist and be non-empty."
    assert isinstance(api_mapping, dict) and api_mapping, "x-api-mapping must exist and be non-empty."


def test_openapi_api_mapping_includes_customer_rating_endpoint() -> None:
    data = _load_openapi()
    mapping = data.get("x-api-mapping", {})

    orders_entries = mapping.get("Orders", []) if isinstance(mapping, dict) else []
    assert any(
        str(entry).strip() == "post /api/v1/orders/{order_id}/customer-rating"
        for entry in orders_entries
    ), "x-api-mapping must include customer rating endpoint under Orders."


def test_all_operations_have_descriptions() -> None:
    data = _load_openapi()

    missing = [
        (method.upper(), path)
        for path, method, operation in _iter_operations(data)
        if not str(operation.get("description", "")).strip()
    ]

    assert not missing, f"Operations missing description: {missing[:20]} (total: {len(missing)})"


def test_secured_operations_document_401_response() -> None:
    data = _load_openapi()

    missing = []
    for path, method, operation in _iter_operations(data):
        if not operation.get("security"):
            continue
        responses = operation.get("responses", {})
        if not isinstance(responses, dict) or "401" not in responses:
            missing.append((method.upper(), path))

    assert not missing, f"Secured operations missing 401 response docs: {missing[:20]} (total: {len(missing)})"
