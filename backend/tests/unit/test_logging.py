import json
import logging

import pytest

from app.core.logging import (
    ConsoleFormatter,
    JSONFormatter,
    log_with_context,
    request_id_var,
)


def _record(message: str = "ORDERS: Order created", **extra: object) -> logging.LogRecord:
    record = logging.LogRecord("app.orders", logging.INFO, __file__, 1, message, None, None)
    for key, value in extra.items():
        setattr(record, key, value)
    return record


def test_log_with_context_puts_context_and_kwargs_under_context(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = logging.getLogger("test.log_with_context")

    with caplog.at_level(logging.INFO, logger="test.log_with_context"):
        log_with_context(logger, "WARNING", "ORDERS: Rejected", context={"a": 1}, b=2)

    record = caplog.records[0]
    assert record.levelno == logging.WARNING
    assert record.getMessage() == "ORDERS: Rejected"
    assert record.__dict__["context"] == {"a": 1, "b": 2}


def test_json_formatter_includes_request_id_and_context() -> None:
    token = request_id_var.set("req-1")
    try:
        output = JSONFormatter().format(_record(context={"order_reference": "ORD-1"}))
    finally:
        request_id_var.reset(token)

    payload = json.loads(output)
    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.orders"
    assert payload["message"] == "ORDERS: Order created"
    assert payload["request_id"] == "req-1"
    assert payload["context"] == {"order_reference": "ORD-1"}
    assert "timestamp" in payload


def test_json_formatter_omits_request_id_outside_a_request() -> None:
    payload = json.loads(JSONFormatter().format(_record()))

    assert "request_id" not in payload


def test_console_formatter_is_readable_and_includes_context() -> None:
    token = request_id_var.set("req-1")
    try:
        line = ConsoleFormatter().format(_record(context={"order_reference": "ORD-1"}))
    finally:
        request_id_var.reset(token)

    assert "INFO" in line
    assert "[req-1]" in line
    assert line.endswith("ORDERS: Order created | order_reference=ORD-1")
