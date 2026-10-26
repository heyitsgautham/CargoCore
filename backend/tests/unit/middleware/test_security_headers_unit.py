"""Tests for the middleware that adds security headers to every HTTP response."""

from httpx import ASGITransport, AsyncClient
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from app.main import app as api_app
from app.middleware.security_headers import HSTS_VALUE, SecurityHeadersMiddleware


def _app(*, hsts: bool) -> Starlette:
    async def plain(_request):
        return JSONResponse({"ok": True})

    async def framed(_request):
        return JSONResponse({"ok": True}, headers={"X-Frame-Options": "SAMEORIGIN"})

    app = Starlette(routes=[Route("/plain", plain), Route("/framed", framed)])
    app.add_middleware(SecurityHeadersMiddleware, hsts=hsts)
    return app


async def _get(app, path: str):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.get(path)


async def test_every_response_gets_the_base_headers() -> None:
    response = await _get(_app(hsts=False), "/plain")

    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "strict-transport-security" not in response.headers


async def test_hsts_is_sent_only_when_enabled() -> None:
    response = await _get(_app(hsts=True), "/plain")

    assert response.headers["strict-transport-security"] == HSTS_VALUE


async def test_a_header_the_route_set_is_left_alone() -> None:
    response = await _get(_app(hsts=False), "/framed")

    assert response.headers.get_list("x-frame-options") == ["SAMEORIGIN"]


async def test_the_api_sends_the_headers_on_its_health_check() -> None:
    response = await _get(api_app, "/health")

    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
