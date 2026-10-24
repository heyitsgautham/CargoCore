import re
import time
import uuid

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware

REQUEST_ID_HEADER = "X-Request-ID"
# Accept a caller's request id only if it is short and plain, so it is safe to log and echo.
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def resolve_request_id(incoming: str | None) -> str:
    """Reuse a well-formed incoming request id, or mint a new one."""
    if incoming and _VALID_REQUEST_ID.match(incoming):
        return incoming
    return uuid.uuid4().hex


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Structured request logging with Loguru.

    Every request gets a request id, taken from a valid X-Request-ID header or
    generated, which is bound to all log records made while the request runs and
    echoed back in the response header. One record per request carries method,
    path, status_code, duration_ms and client as structured fields.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = resolve_request_id(request.headers.get(REQUEST_ID_HEADER))
        start = time.perf_counter()

        with logger.contextualize(request_id=request_id):
            try:
                response = await call_next(request)
            except Exception:
                logger.bind(method=request.method, path=request.url.path).exception(
                    "Unhandled exception"
                )
                raise

            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            request_log = logger.bind(
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                client=request.client.host if request.client else "unknown",
            )
            if response.status_code >= 500:
                request_log.error("Request failed")
            else:
                request_log.info("Request completed")

        response.headers[REQUEST_ID_HEADER] = request_id
        return response
