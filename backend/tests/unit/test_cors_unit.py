"""CORS preflight behavior of the real app, which replaced the old print-only CORS scripts."""

from httpx import ASGITransport, AsyncClient

from app.main import app


async def _preflight(origin: str):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        return await client.options(
            "/api/v1/auth/login",
            headers={"Origin": origin, "Access-Control-Request-Method": "POST"},
        )


async def test_preflight_allows_the_vite_dev_origin() -> None:
    response = await _preflight("http://localhost:5173")

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"


async def test_preflight_allows_the_capacitor_driver_app() -> None:
    response = await _preflight("capacitor://localhost")

    assert response.headers["access-control-allow-origin"] == "capacitor://localhost"


async def test_preflight_rejects_an_unknown_origin() -> None:
    response = await _preflight("https://evil.example")

    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers
