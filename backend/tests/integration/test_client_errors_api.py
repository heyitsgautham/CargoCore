"""The endpoint the web app reports browser errors to."""

import pytest
from loguru import logger

from app.routers.client_errors import REPORTS_PER_MINUTE, reset_rate_limits

URL = "/api/v1/client-errors"


@pytest.fixture(autouse=True)
def _fresh_limits():
    reset_rate_limits()
    yield
    reset_rate_limits()


@pytest.fixture()
def captured_logs():
    records = []
    sink = logger.add(lambda message: records.append(message.record), level="WARNING")
    yield records
    logger.remove(sink)


async def test_report_lands_in_the_logs_with_its_scope_and_context(client, captured_logs):
    response = await client.post(
        URL,
        json={
            "message": "Cannot read properties of undefined (reading 'id')",
            "scope": "picking",
            "stack": "TypeError at PickWaveCard.vue:12",
            "url": "http://localhost:5173/warehouse/picking",
            "context": {"orderId": "QC-DEMO103", "attempt": 2},
        },
    )

    assert response.status_code == 202
    record = next(r for r in captured_logs if r["extra"].get("source") == "client")
    assert record["level"].name == "ERROR"
    assert record["extra"]["scope"] == "picking"
    assert record["extra"]["ctx_orderId"] == "QC-DEMO103"
    assert "PickWaveCard.vue:12" in record["message"]


async def test_warnings_are_logged_at_warning_level(client, captured_logs):
    response = await client.post(URL, json={"level": "warning", "message": "Slow map tiles"})

    assert response.status_code == 202
    record = next(r for r in captured_logs if r["extra"].get("source") == "client")
    assert record["level"].name == "WARNING"


@pytest.mark.parametrize(
    "payload",
    [
        {"message": ""},
        {"message": "x" * 2001},
        {"message": "boom", "level": "critical"},
        {"message": "boom", "scope": "bad scope!"},
        {"message": "boom", "context": {f"k{i}": i for i in range(21)}},
        {"message": "boom", "context": {"nested": {"a": 1}}},
    ],
)
async def test_malformed_reports_are_refused(client, payload):
    response = await client.post(URL, json=payload)
    assert response.status_code == 422


async def test_a_client_sending_too_many_reports_is_throttled(client):
    for _ in range(REPORTS_PER_MINUTE):
        assert (await client.post(URL, json={"message": "boom"})).status_code == 202

    response = await client.post(URL, json={"message": "boom"})

    assert response.status_code == 429
