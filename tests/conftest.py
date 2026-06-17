from __future__ import annotations

import json
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, AsyncGenerator, Callable

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from pydantic.warnings import PydanticDeprecatedSince20
except Exception:  # pragma: no cover
    PydanticDeprecatedSince20 = DeprecationWarning

warnings.simplefilter("ignore", PydanticDeprecatedSince20)

warnings.filterwarnings(
    "ignore",
    message=r"Support for class-based `config` is deprecated, use ConfigDict instead\\.",
    category=PydanticDeprecatedSince20,
)
warnings.filterwarnings(
    "ignore",
    message=r"Support for class-based `config` is deprecated, use ConfigDict instead\\.",
    category=Warning,
    module=r"app\.schemas\.logistics",
)

from app.database import get_db, get_ro_db  # noqa: E402
from app.dependencies import get_current_user  # noqa: E402
from app.main import app  # noqa: E402
from app.utils.redis import get_redis  # noqa: E402

REPORTS_DIR = ROOT_DIR / "tests" / "reports"
EVIDENCE_JSON_PATH = REPORTS_DIR / "API_TEST_EVIDENCE.json"
MISMATCH_JSON_PATH = REPORTS_DIR / "API_MISMATCH_CASES.json"

_EVIDENCE_ROWS: list[dict[str, Any]] = []
_MISMATCH_ROWS: list[dict[str, Any]] = []


class DummyRedis:
    async def get(self, _key: str) -> None:
        return None

    async def setex(self, _key: str, _ttl: int, _value: str) -> bool:
        return True

    async def delete(self, _key: str) -> int:
        return 1


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "model_dump"):
        return _json_safe(value.model_dump())
    if hasattr(value, "dict"):
        return _json_safe(value.dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return repr(value)


def _build_fake_user(role_name: str = "LOGISTIC_MANAGER") -> SimpleNamespace:
    now = datetime.now(timezone.utc)
    return SimpleNamespace(
        id="11111111-1111-1111-1111-111111111111",
        name="Test User",
        username="test.user",
        email="test.user@example.com",
        phone="9999999999",
        address="123 Test Street",
        role=SimpleNamespace(name=role_name),
        warehouse_id=None,
        is_active=True,
        approval_status="APPROVED",
        company_name=None,
        tax_id=None,
        contact_person=None,
        business_email=None,
        business_phone=None,
        created_at=now,
    )


async def _override_db() -> AsyncGenerator[Any, None]:
    yield SimpleNamespace(name="dummy-db")


async def _override_redis() -> AsyncGenerator[DummyRedis, None]:
    yield DummyRedis()


@pytest_asyncio.fixture()
async def client() -> AsyncGenerator[AsyncClient, None]:
    app.dependency_overrides[get_db] = _override_db
    app.dependency_overrides[get_ro_db] = _override_db
    app.dependency_overrides[get_redis] = _override_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture()
def fake_user() -> SimpleNamespace:
    return _build_fake_user(role_name="LOGISTIC_MANAGER")


@pytest_asyncio.fixture()
async def authorized_client(
    client: AsyncClient,
    fake_user: SimpleNamespace,
) -> AsyncGenerator[AsyncClient, None]:
    async def _override_current_user() -> Any:
        return fake_user

    app.dependency_overrides[get_current_user] = _override_current_user
    yield client
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture()
def dependency_override_manager() -> Callable[[Any, Any], None]:
    original_values: dict[Any, Any] = {}

    def _set_override(dependency: Any, override: Any) -> None:
        if dependency not in original_values:
            original_values[dependency] = app.dependency_overrides.get(dependency)
        app.dependency_overrides[dependency] = override

    yield _set_override

    for dependency, original in original_values.items():
        if original is None:
            app.dependency_overrides.pop(dependency, None)
        else:
            app.dependency_overrides[dependency] = original


@pytest.fixture()
def record_evidence(request: pytest.FixtureRequest) -> Callable[..., None]:
    def _record(
        case_id: str,
        endpoint: str,
        input_data: Any,
        expected_output: Any,
        actual_output: Any,
        status: str,
        notes: str | None = None,
    ) -> None:
        _EVIDENCE_ROWS.append(
            {
                "case_id": case_id,
                "test_name": request.node.name,
                "endpoint": endpoint,
                "input": _json_safe(input_data),
                "expected_output": _json_safe(expected_output),
                "actual_output": _json_safe(actual_output),
                "status": status,
                "notes": notes,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    return _record


@pytest.fixture()
def record_mismatch(request: pytest.FixtureRequest) -> Callable[..., None]:
    def _record(
        case_id: str,
        endpoint: str,
        input_data: Any,
        expected_output: Any,
        actual_output: Any,
        difference_summary: str,
    ) -> None:
        _MISMATCH_ROWS.append(
            {
                "case_id": case_id,
                "test_name": request.node.name,
                "endpoint": endpoint,
                "input": _json_safe(input_data),
                "expected_output": _json_safe(expected_output),
                "actual_output": _json_safe(actual_output),
                "difference_summary": difference_summary,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    return _record


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    evidence_rows = sorted(_EVIDENCE_ROWS, key=lambda row: (row["case_id"], row["test_name"]))
    mismatch_rows = sorted(_MISMATCH_ROWS, key=lambda row: (row["case_id"], row["test_name"]))

    EVIDENCE_JSON_PATH.write_text(
        json.dumps(evidence_rows, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
    MISMATCH_JSON_PATH.write_text(
        json.dumps(mismatch_rows, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )
