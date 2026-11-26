import logging

import pytest
from fastapi.testclient import TestClient

from app.core.logging import ACCESS_LOGGER_NAME

HEALTH_URL = "/api/v1/health"


def test_response_includes_generated_request_id(client: TestClient) -> None:
    response = client.get(HEALTH_URL)

    assert len(response.headers["X-Request-ID"]) == 32


def test_well_formed_incoming_request_id_is_reused(client: TestClient) -> None:
    response = client.get(HEALTH_URL, headers={"X-Request-ID": "trace-abc-123"})

    assert response.headers["X-Request-ID"] == "trace-abc-123"


def test_malformed_incoming_request_id_is_replaced(client: TestClient) -> None:
    response = client.get(HEALTH_URL, headers={"X-Request-ID": "bad id with spaces"})

    assert response.headers["X-Request-ID"] != "bad id with spaces"
    assert len(response.headers["X-Request-ID"]) == 32


def test_each_request_writes_one_access_log_line(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO, logger=ACCESS_LOGGER_NAME):
        client.get(HEALTH_URL)

    access_logs = [record for record in caplog.records if record.name == ACCESS_LOGGER_NAME]
    assert len(access_logs) == 1
    assert access_logs[0].levelno == logging.INFO
    context = access_logs[0].__dict__["context"]
    assert context["method"] == "GET"
    assert context["path"] == HEALTH_URL
    assert context["status_code"] == 200


def test_business_rejection_is_logged_as_warning(
    client: TestClient, caplog: pytest.LogCaptureFixture
) -> None:
    with caplog.at_level(logging.INFO):
        client.get("/api/v1/products/00000000-0000-0000-0000-000000000000")

    rejection = next(r for r in caplog.records if "Request rejected" in r.getMessage())
    assert rejection.levelno == logging.WARNING
    assert rejection.__dict__["context"]["status_code"] == 404
