"""Centralized exception handlers.

Every error response has the same shape:
    {"error": {"code": "...", "message": "...", "details": [...] | null}}
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppError
from app.core.logging import log_with_context
from app.core.schemas import ErrorBody, ErrorDetail, ErrorResponse

logger = logging.getLogger(__name__)


def _error_response(
    status_code: int, code: str, message: str, details: list[ErrorDetail] | None = None
) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details))
    return JSONResponse(status_code=status_code, content=body.model_dump(mode="json"))


async def handle_app_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, AppError)
    log_with_context(
        logger,
        "ERROR" if exc.status_code >= 500 else "WARNING",
        f"APP: Request rejected with {exc.code} (error_handlers.py handle_app_error)",
        context={
            "error_code": exc.code,
            "status_code": exc.status_code,
            "error_message": exc.message,
            "path": request.url.path,
        },
    )
    return _error_response(exc.status_code, exc.code, exc.message, exc.details)


async def handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, RequestValidationError)
    details = [
        ErrorDetail(field=".".join(str(part) for part in error["loc"]), message=error["msg"])
        for error in exc.errors()
    ]
    log_with_context(
        logger,
        "WARNING",
        "APP: Invalid request data (error_handlers.py handle_validation_error)",
        context={"fields": [detail.field for detail in details], "path": request.url.path},
    )
    return _error_response(
        status.HTTP_422_UNPROCESSABLE_CONTENT, "validation_error", "Invalid request data.", details
    )


async def handle_http_exception(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, StarletteHTTPException)
    code = "not_found" if exc.status_code == status.HTTP_404_NOT_FOUND else "http_error"
    return _error_response(exc.status_code, code, str(exc.detail))


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    log_with_context(
        logger,
        "ERROR",
        "APP: Unexpected exception (error_handlers.py handle_unexpected_error)",
        context={"method": request.method, "path": request.url.path},
        exc_info=exc,
    )
    return _error_response(
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        "internal_error",
        "An unexpected error occurred. Please try again later.",
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, handle_app_error)
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(StarletteHTTPException, handle_http_exception)
    app.add_exception_handler(Exception, handle_unexpected_error)
