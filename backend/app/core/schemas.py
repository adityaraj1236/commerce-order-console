"""Shared API schemas.

`ErrorResponse` is the single source of truth for the error shape: the error handlers
build responses with it, and routes reference it so Swagger documents the real format.
"""

from typing import Any

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


def error_responses(*status_codes: int) -> dict[int | str, dict[str, Any]]:
    """Build a route's `responses=` entry documenting the given error status codes.

    Usage: @router.get("/{id}", responses=error_responses(404, 422))
    """
    descriptions = {
        404: "Resource not found",
        409: "Conflict with the current state (e.g. insufficient stock, invalid transition)",
        422: "Invalid request data",
    }
    return {
        code: {"model": ErrorResponse, "description": descriptions.get(code, "Error")}
        for code in status_codes
    }
