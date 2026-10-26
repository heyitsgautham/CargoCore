"""Security headers on every HTTP response.

The API only returns JSON and a few HTML documents that the web app fetches and renders
itself, so no response needs to be sniffed as another type or shown inside a frame.
HSTS is sent only in production, where the API is served over HTTPS.
"""

from starlette.types import ASGIApp, Message, Receive, Scope, Send

BASE_HEADERS: dict[str, str] = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}
HSTS_VALUE = "max-age=31536000; includeSubDomains"


class SecurityHeadersMiddleware:
    """Add the security headers to HTTP responses that do not already set them."""

    def __init__(self, app: ASGIApp, *, hsts: bool = False) -> None:
        self.app = app
        headers = dict(BASE_HEADERS)
        if hsts:
            headers["Strict-Transport-Security"] = HSTS_VALUE
        self.headers = [(name.lower().encode(), value.encode()) for name, value in headers.items()]

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                existing = {name.lower() for name, _ in message.get("headers", [])}
                extra = [(name, value) for name, value in self.headers if name not in existing]
                message["headers"] = [*message.get("headers", []), *extra]
            await send(message)

        await self.app(scope, receive, send_with_headers)
