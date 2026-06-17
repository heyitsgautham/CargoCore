from __future__ import annotations

from pathlib import Path
import re

import yaml
from fastapi.routing import APIRoute

from app.main import app

OPENAPI_YAML = Path(__file__).resolve().parents[1] / "api-docs" / "openapi.swagger.yaml"


def _load_openapi() -> dict:
    assert OPENAPI_YAML.exists(), "OpenAPI YAML not found. Generate tests/api-docs/openapi.swagger.yaml first."
    with OPENAPI_YAML.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def _collect_documented_operations(openapi_data: dict) -> set[tuple[str, str]]:
    documented: set[tuple[str, str]] = set()
    for path, methods in openapi_data.get("paths", {}).items():
        for method in methods.keys():
            method_name = str(method).lower()
            if method_name in {"get", "post", "put", "delete", "patch"}:
                documented.add((str(path), method_name))
    return documented


def _collect_backend_operations() -> set[tuple[str, str]]:
    backend: set[tuple[str, str]] = set()

    def _normalize_path(path: str) -> str:
        # FastAPI route objects may include path converters like {item_id:uuid}
        # while OpenAPI exports use {item_id}. Normalize before comparison.
        return re.sub(r"\{([^}:]+):[^}]+\}", r"{\1}", path)

    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if not route.include_in_schema:
            continue
        if not (route.path.startswith("/api/v1") or route.path == "/health"):
            continue

        for method in route.methods or []:
            method_name = str(method).lower()
            if method_name in {"head", "options"}:
                continue
            backend.add((_normalize_path(route.path), method_name))
    return backend


def test_openapi_covers_all_backend_routes() -> None:
    openapi_data = _load_openapi()
    documented = _collect_documented_operations(openapi_data)
    backend = _collect_backend_operations()

    missing = sorted(backend - documented)

    assert backend, "No backend operations discovered from FastAPI routes."
    assert not missing, (
        "OpenAPI YAML is missing backend operations. First missing entries: "
        f"{missing[:30]} (total missing: {len(missing)})."
    )
