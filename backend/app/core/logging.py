"""Centralized logging, following the same conventions as ambisquare_backend.

Usage everywhere in the app:

    log_with_context(
        logger,
        "INFO",
        "ORDERS: Order created (service.py create_order)",
        context={"order_reference": order.order_reference},
    )

Environments:
- development: readable console output, plus one pretty-JSON file per level in `logs/`
  (info.log, access.log, warn.log, error.log), rotated at 50 MB.
- anything else (production, test): one JSON object per line on stdout.

Only three levels are used: INFO, WARNING, ERROR.
"""

import json
import logging
import logging.handlers
import sys
from contextvars import ContextVar
from pathlib import Path
from typing import Any

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

ACCESS_LOGGER_NAME = "app.access"

# Standard LogRecord attributes, plus uvicorn's ANSI-coloured duplicate of the message.
_RESERVED_LOG_RECORD_ATTRS = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__) | {
    "color_message"
}


def _extra_fields(record: logging.LogRecord) -> dict[str, Any]:
    return {
        key: value
        for key, value in record.__dict__.items()
        if key not in _RESERVED_LOG_RECORD_ATTRS
    }


class JSONFormatter(logging.Formatter):
    def __init__(self, *, pretty: bool = False) -> None:
        super().__init__()
        self._indent = 2 if pretty else None

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        request_id = request_id_var.get()
        if request_id is not None:
            payload["request_id"] = request_id

        payload.update(_extra_fields(record))

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str, indent=self._indent)


class ConsoleFormatter(logging.Formatter):
    """Readable one-line format for the development console."""

    def __init__(self) -> None:
        super().__init__(datefmt="%H:%M:%S")

    def format(self, record: logging.LogRecord) -> str:
        line = (
            f"{self.formatTime(record, self.datefmt)} {record.levelname:<7} "
            f"[{request_id_var.get() or '-'}] {record.getMessage()}"
        )
        context = _extra_fields(record).get("context") or {}
        if context:
            line += " | " + " ".join(f"{key}={value}" for key, value in context.items())
        if record.exc_info:
            line += "\n" + self.formatException(record.exc_info)
        return line


class _LevelRangeFilter(logging.Filter):
    def __init__(self, min_level: int, max_level: int | None = None) -> None:
        super().__init__()
        self.min_level = min_level
        self.max_level = max_level

    def filter(self, record: logging.LogRecord) -> bool:
        if self.max_level is not None:
            return self.min_level <= record.levelno <= self.max_level
        return record.levelno >= self.min_level


class _AccessLogFilter(logging.Filter):
    """Selects (or excludes) the per-request access log lines written by the middleware."""

    def __init__(self, *, access_only: bool) -> None:
        super().__init__()
        self.access_only = access_only

    def filter(self, record: logging.LogRecord) -> bool:
        return (record.name == ACCESS_LOGGER_NAME) == self.access_only


def _file_handler(logs_dir: Path, filename: str, *filters: logging.Filter) -> logging.Handler:
    handler = logging.handlers.RotatingFileHandler(
        logs_dir / filename, maxBytes=50 * 1024 * 1024, backupCount=30, encoding="utf-8"
    )
    handler.setFormatter(JSONFormatter(pretty=True))
    for log_filter in filters:
        handler.addFilter(log_filter)
    # Pretty-printed entries span multiple lines; a blank line keeps entries distinct.
    handler.terminator = "\n\n"
    return handler


def setup_logging(environment: str) -> None:
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.setLevel(logging.INFO)

    if environment == "development":
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ConsoleFormatter())
        root_logger.addHandler(console_handler)

        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        root_logger.addHandler(
            _file_handler(
                logs_dir,
                "info.log",
                _LevelRangeFilter(logging.INFO, logging.INFO),
                _AccessLogFilter(access_only=False),
            )
        )
        root_logger.addHandler(
            _file_handler(logs_dir, "access.log", _AccessLogFilter(access_only=True))
        )
        root_logger.addHandler(
            _file_handler(logs_dir, "warn.log", _LevelRangeFilter(logging.WARNING, logging.WARNING))
        )
        root_logger.addHandler(
            _file_handler(logs_dir, "error.log", _LevelRangeFilter(logging.ERROR))
        )
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        root_logger.addHandler(handler)

    # We log our own structured access line per request; uvicorn's access logger
    # would otherwise duplicate it in a different, non-JSON format.
    logging.getLogger("uvicorn.access").disabled = True

    # Route uvicorn's own logs (startup messages, tracebacks) through our handlers.
    for uvicorn_logger_name in ("uvicorn", "uvicorn.error"):
        uvicorn_logger = logging.getLogger(uvicorn_logger_name)
        uvicorn_logger.handlers.clear()
        uvicorn_logger.propagate = True


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    context: dict[str, Any] | None = None,
    exc_info: BaseException | bool | None = None,
    **kwargs: Any,
) -> None:
    full_context = dict(context or {})
    full_context.update(kwargs)
    log_level = logging.getLevelNamesMapping().get(level.upper(), logging.INFO)
    logger.log(log_level, message, extra={"context": full_context}, exc_info=exc_info)
