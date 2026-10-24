import time

from fastapi import Request, Response
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Structured JSON request / response logging using loguru.
    Logs: method, path, status_code, duration_ms for every request.
    Sensitive paths (login, register) skip body logging.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception:
            import traceback
            logger.error(
                f"UNHANDLED EXCEPTION {request.method} {request.url.path}\n"
                + traceback.format_exc()
            )
            raise

        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        if response.status_code >= 500:
            logger.error(
                {
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                }
            )
        else:
            logger.info(
                {
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                    "client": request.client.host if request.client else "unknown",
                }
            )
        return response
