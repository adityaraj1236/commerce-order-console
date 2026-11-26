import logging
import re
import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import ACCESS_LOGGER_NAME, log_with_context, request_id_var

REQUEST_ID_HEADER = "X-Request-ID"
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

access_logger = logging.getLogger(ACCESS_LOGGER_NAME)


def _resolve_request_id(scope: Scope) -> str:
    """Reuse a well-formed incoming X-Request-ID, otherwise generate a new one."""
    for name, value in scope["headers"]:
        if name == b"x-request-id":
            candidate = value.decode("latin-1")
            if _VALID_REQUEST_ID.fullmatch(candidate):
                return candidate
    return uuid.uuid4().hex


class RequestContextMiddleware:
    """Assigns a request ID, echoes it in the response header and writes one access log line.

    The request ID is not reset afterwards on purpose: the 500 handler runs outside this
    middleware and must still see it. Each request runs in its own context, so it cannot leak.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _resolve_request_id(scope)
        request_id_var.set(request_id)
        status_code = 500
        started_at = time.perf_counter()

        async def send_with_request_id(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                MutableHeaders(scope=message).append(REQUEST_ID_HEADER, request_id)
            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            log_with_context(
                access_logger,
                "ERROR" if status_code >= 500 else "INFO",
                "HTTP request",
                context={
                    "method": scope["method"],
                    "path": scope["path"],
                    "status_code": status_code,
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 1),
                },
            )
