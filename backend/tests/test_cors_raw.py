import asyncio

from app.main import app


class DummyReceive:
    async def __call__(self):
        return {"type": "http.request"}

class DummySend:
    async def __call__(self, message):
        print("Sent:", message)

async def test_app():
    scope = {
        "type": "http",
        "method": "OPTIONS",
        "path": "/api/v1/auth/login",
        "headers": [
            (b"host", b"localhost:8000"),
            (b"origin", b"http://localhost:5174"),
            (b"access-control-request-method", b"POST"),
        ],
    }
    await app(scope, DummyReceive(), DummySend())

asyncio.run(test_app())
