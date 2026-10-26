"""Collects browser-side errors so they land in the API's structured logs."""

import time
from collections import OrderedDict

from fastapi import APIRouter, HTTPException, Request, status
from loguru import logger

from app.schemas.client_errors import ClientErrorReport

router = APIRouter(prefix="/api/v1/client-errors", tags=["Client errors"])

# Fixed one-minute windows per client address, kept for the most recent 1,000 addresses.
REPORTS_PER_MINUTE = 30
_MAX_TRACKED_CLIENTS = 1000
_windows: "OrderedDict[str, tuple[int, int]]" = OrderedDict()


def _allow(client: str, now: float | None = None) -> bool:
    minute = int((now if now is not None else time.time()) // 60)
    window, count = _windows.pop(client, (minute, 0))
    if window != minute:
        window, count = minute, 0
    count += 1
    _windows[client] = (window, count)
    while len(_windows) > _MAX_TRACKED_CLIENTS:
        _windows.popitem(last=False)
    return count <= REPORTS_PER_MINUTE


def reset_rate_limits() -> None:
    _windows.clear()


@router.post(
    "",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Record an error raised in the web or driver app",
    description=(
        "Writes the report to the API's structured log at error or warning level, tagged with "
        "source=client, its scope and context fields. Each client address may send 30 reports "
        "a minute; more get 429."
    ),
)
async def report_client_error(report: ClientErrorReport, request: Request) -> dict:
    client = request.client.host if request.client else "unknown"
    if not _allow(client):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Too many error reports")

    entry = logger.bind(
        source="client",
        scope=report.scope,
        url=report.url,
        user_agent=report.user_agent or request.headers.get("user-agent"),
        release=report.release,
        client=client,
        **{f"ctx_{key}": value for key, value in report.context.items()},
    )
    message = f"Client {report.level}: {report.message}"
    if report.stack:
        message = f"{message}\n{report.stack}"
    if report.level == "warning":
        entry.warning(message)
    else:
        entry.error(message)
    return {"status": "accepted"}
