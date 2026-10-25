"""Fixtures for flow tests: a seeded world and no outbound network calls."""

import httpx
import pytest
import pytest_asyncio

from tests.factories import build_world


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    """Fail every real HTTP call, so OSRM, Nominatim and Daily lookups take their offline paths."""

    async def refuse(self, request):
        raise httpx.ConnectError(f"network disabled in tests: {request.url}", request=request)

    monkeypatch.setattr(httpx.AsyncHTTPTransport, "handle_async_request", refuse)


@pytest_asyncio.fixture()
async def world(db_session):
    return await build_world(db_session)
