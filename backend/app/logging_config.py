"""Loguru setup shared by the API process.

configure_logging() replaces Loguru's default stderr sink with one stdout sink.
With LOG_JSON on, every record is one JSON object per line, which container log
collectors can parse. Records from the standard logging module, such as Uvicorn,
SQLAlchemy and app.utils.geocoding, are routed through the same sink.
"""

from __future__ import annotations

import inspect
import logging
import sys

from loguru import logger

_HUMAN_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
    " {extra}"
)


class InterceptHandler(logging.Handler):
    """Forward standard-library log records to Loguru with the caller's location."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = inspect.currentframe(), 0
        while frame and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def configure_logging(level: str = "INFO", json_logs: bool = False, sink=None) -> None:
    """Install the single Loguru sink and route stdlib logging into it."""
    logger.remove()
    logger.add(
        sink if sink is not None else sys.stdout,
        level=level.upper(),
        serialize=json_logs,
        format="{message}" if json_logs else _HUMAN_FORMAT,
        backtrace=False,
        diagnose=False,
    )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"):
        std_logger = logging.getLogger(name)
        std_logger.handlers = [InterceptHandler()]
        std_logger.propagate = False
