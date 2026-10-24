import io
import json
import logging

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from loguru import logger

from app.config import Settings
from app.logging_config import configure_logging
from app.middleware.logging_middleware import (
    REQUEST_ID_HEADER,
    LoggingMiddleware,
    resolve_request_id,
)


@pytest.fixture()
def json_log_stream():
    stream = io.StringIO()
    configure_logging(level="DEBUG", json_logs=True, sink=stream)
    yield stream
    configure_logging()


def _records(stream: io.StringIO) -> list[dict]:
    return [json.loads(line)["record"] for line in stream.getvalue().splitlines() if line]


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(LoggingMiddleware)

    @app.get("/ok")
    async def ok():
        logger.info("inside handler")
        return {"ok": True}

    return app


def test_resolve_request_id_keeps_a_valid_incoming_id() -> None:
    assert resolve_request_id("abc-123_DEF.9") == "abc-123_DEF.9"


@pytest.mark.parametrize("incoming", [None, "", "has spaces", "x" * 65, "evil\nnewline"])
def test_resolve_request_id_replaces_missing_or_unsafe_ids(incoming) -> None:
    generated = resolve_request_id(incoming)

    assert generated != incoming
    assert len(generated) == 32
    int(generated, 16)


def test_json_sink_writes_one_parseable_record_per_line(json_log_stream) -> None:
    logger.bind(order_id="o-1").warning("geocoding failed")

    [record] = _records(json_log_stream)
    assert record["message"] == "geocoding failed"
    assert record["level"]["name"] == "WARNING"
    assert record["extra"] == {"order_id": "o-1"}


def test_level_filter_drops_lower_records() -> None:
    stream = io.StringIO()
    configure_logging(level="WARNING", json_logs=True, sink=stream)
    try:
        logger.info("hidden")
        logger.error("shown")
    finally:
        configure_logging()

    assert [r["message"] for r in _records(stream)] == ["shown"]


def test_stdlib_logging_is_routed_into_loguru(json_log_stream) -> None:
    logging.getLogger("app.utils.geocoding").warning("from stdlib %s", "logging")

    [record] = _records(json_log_stream)
    assert record["message"] == "from stdlib logging"
    assert record["level"]["name"] == "WARNING"


async def test_middleware_logs_request_fields_and_echoes_request_id(json_log_stream) -> None:
    async with AsyncClient(transport=ASGITransport(app=_app()), base_url="http://test") as client:
        response = await client.get("/ok", headers={REQUEST_ID_HEADER: "req-42"})

    assert response.status_code == 200
    assert response.headers[REQUEST_ID_HEADER] == "req-42"

    records = _records(json_log_stream)
    handler_record = next(r for r in records if r["message"] == "inside handler")
    request_record = next(r for r in records if r["message"] == "Request completed")

    assert handler_record["extra"]["request_id"] == "req-42"
    assert request_record["extra"]["request_id"] == "req-42"
    assert request_record["extra"]["method"] == "GET"
    assert request_record["extra"]["path"] == "/ok"
    assert request_record["extra"]["status_code"] == 200
    assert request_record["extra"]["duration_ms"] >= 0


async def test_middleware_generates_a_request_id_when_none_is_sent(json_log_stream) -> None:
    async with AsyncClient(transport=ASGITransport(app=_app()), base_url="http://test") as client:
        response = await client.get("/ok")

    assert len(response.headers[REQUEST_ID_HEADER]) == 32


async def test_middleware_logs_unhandled_exceptions_and_reraises(json_log_stream) -> None:
    app = FastAPI()
    app.add_middleware(LoggingMiddleware)

    @app.get("/boom")
    async def boom():
        raise RuntimeError("kaboom")

    async with AsyncClient(
        transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test"
    ) as client:
        response = await client.get("/boom")

    assert response.status_code == 500
    record = next(r for r in _records(json_log_stream) if r["message"] == "Unhandled exception")
    assert record["level"]["name"] == "ERROR"
    assert record["extra"]["path"] == "/boom"
    assert record["exception"]["type"] == "RuntimeError"


@pytest.mark.parametrize(
    ("app_env", "log_json", "expected"),
    [
        ("development", None, False),
        ("production", None, True),
        ("production", "", True),
        ("production", False, False),
        ("development", True, True),
    ],
)
def test_json_logging_defaults_to_on_in_production(app_env, log_json, expected) -> None:
    settings = Settings(app_env=app_env, log_json=log_json, _env_file=None)
    assert settings.log_json_enabled is expected
