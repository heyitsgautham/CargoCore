from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import yaml
from httpx import ASGITransport, AsyncClient

ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.database import get_db, get_ro_db  # noqa: E402
from app.main import app  # noqa: E402
from app.utils.redis import get_redis  # noqa: E402

OPENAPI_PATH = ROOT_DIR / "tests" / "api-docs" / "openapi.swagger.yaml"
EVIDENCE_PATH = ROOT_DIR / "tests" / "reports" / "API_TEST_EVIDENCE.json"
OUTPUT_PATH = ROOT_DIR / "tests" / "reports" / "MISSING_ENDPOINT_STATUS_SCAN.json"


def normalize_operation(operation: str) -> str:
    operation = operation.strip()
    if not operation:
        return ""
    parts = operation.split(maxsplit=1)
    if len(parts) != 2:
        return operation.upper()
    method, path = parts
    return f"{method.upper()} {path.strip()}"


class DummyResult:
    def scalar_one_or_none(self):
        return None

    def scalar_one(self):
        return 0

    def scalars(self):
        return self

    def all(self):
        return []

    def first(self):
        return None


class DummyDB:
    async def execute(self, *args, **kwargs):
        return DummyResult()

    async def commit(self):
        return None

    async def rollback(self):
        return None

    async def flush(self):
        return None

    async def refresh(self, *args, **kwargs):
        return None

    def add(self, *args, **kwargs):
        return None

    def add_all(self, *args, **kwargs):
        return None


class DummyRedis:
    async def get(self, _key: str):
        return None

    async def setex(self, _key: str, _ttl: int, _value: str):
        return True

    async def delete(self, _key: str):
        return 1


async def _override_db():
    yield DummyDB()


async def _override_redis():
    yield DummyRedis()


def auth_required(operation_spec: dict, global_security: list) -> bool:
    if "security" in operation_spec:
        operation_security = operation_spec.get("security")
        if operation_security == []:
            return False
        return True
    return bool(global_security)


def build_probe_path(path_template: str, parameters: list[dict]) -> str:
    result = path_template
    for param in parameters:
        if param.get("in") != "path":
            continue
        name = str(param.get("name", "")).strip()
        schema = param.get("schema", {}) if isinstance(param.get("schema"), dict) else {}
        value = "probe"
        if schema.get("format") == "uuid":
            value = "not-a-uuid"
        elif schema.get("type") in {"integer", "number"}:
            value = "not-a-number"
        elif schema.get("type") == "boolean":
            value = "not-a-bool"

        result = result.replace("{" + name + "}", value)
    return result


def build_probe_query(parameters: list[dict]) -> dict[str, str]:
    query: dict[str, str] = {}
    for param in parameters:
        if param.get("in") != "query":
            continue
        name = str(param.get("name", "")).strip()
        schema = param.get("schema", {}) if isinstance(param.get("schema"), dict) else {}

        if schema.get("format") == "uuid":
            query[name] = "bad-uuid"
        elif schema.get("type") in {"integer", "number"}:
            query[name] = "bad-number"
        elif schema.get("type") == "boolean":
            query[name] = "bad-bool"
    return query


def documented_statuses(operation_spec: dict) -> set[int]:
    statuses: set[int] = set()
    responses = operation_spec.get("responses", {}) if isinstance(operation_spec.get("responses"), dict) else {}
    for code in responses:
        code_text = str(code)
        if code_text.isdigit():
            statuses.add(int(code_text))
    return statuses


async def run_scan() -> list[dict]:
    openapi = yaml.safe_load(OPENAPI_PATH.read_text(encoding="utf-8"))
    evidence_rows = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))

    tested_operations = {
        normalize_operation(str(row.get("endpoint", "")))
        for row in evidence_rows
        if str(row.get("endpoint", "")).strip()
    }

    global_security = openapi.get("security", []) if isinstance(openapi, dict) else []

    missing_operations: list[tuple[str, str, str, dict, list[dict]]] = []
    paths = openapi.get("paths", {}) if isinstance(openapi, dict) else {}
    for path, path_item in paths.items():
        if not isinstance(path_item, dict):
            continue

        path_level_params = path_item.get("parameters", []) if isinstance(path_item.get("parameters"), list) else []

        for method, operation_spec in path_item.items():
            method_upper = str(method).upper()
            if method_upper not in {"GET", "POST", "PUT", "PATCH", "DELETE"}:
                continue
            if not isinstance(operation_spec, dict):
                continue

            operation = normalize_operation(f"{method_upper} {path}")
            if operation in tested_operations:
                continue

            operation_params = (
                operation_spec.get("parameters", []) if isinstance(operation_spec.get("parameters"), list) else []
            )
            combined_params = [*path_level_params, *operation_params]
            missing_operations.append((operation, path, method_upper, operation_spec, combined_params))

    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_ro_db] = _override_db
    app.dependency_overrides[get_redis] = _override_redis

    results: list[dict] = []
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            for operation, path, method, operation_spec, params in missing_operations:
                requires_auth = auth_required(operation_spec, global_security)
                url = build_probe_path(path, params)
                query = build_probe_query(params)

                payload = None
                request_body = (
                    operation_spec.get("requestBody", {}) if isinstance(operation_spec.get("requestBody"), dict) else {}
                )
                if method in {"POST", "PUT", "PATCH"} and bool(request_body.get("required")):
                    payload = {}

                kwargs: dict = {"params": query}
                if payload is not None:
                    kwargs["json"] = payload

                try:
                    response = await client.request(method, url, **kwargs)
                    actual_status = response.status_code
                except Exception:
                    actual_status = 599

                expected_status_set = documented_statuses(operation_spec)
                expected_status_set.add(422)
                if requires_auth:
                    expected_status_set.add(401)

                results.append(
                    {
                        "operation": operation,
                        "url": url,
                        "method": method,
                        "auth_required": requires_auth,
                        "expected_statuses": sorted(expected_status_set),
                        "actual_status": actual_status,
                        "mismatch": actual_status not in expected_status_set,
                    }
                )
    finally:
        app.dependency_overrides.clear()

    return results


def main() -> None:
    results = asyncio.run(run_scan())
    OUTPUT_PATH.write_text(json.dumps(results, indent=2), encoding="utf-8")

    mismatches = [row for row in results if row.get("mismatch")]
    print(f"missing_ops_total {len(results)}")
    print(f"mismatch_total {len(mismatches)}")
    print(f"output_file {OUTPUT_PATH}")
    for row in mismatches[:20]:
        print(
            "MISMATCH",
            row.get("operation"),
            "actual",
            row.get("actual_status"),
            "expected",
            row.get("expected_statuses"),
        )


if __name__ == "__main__":
    main()
