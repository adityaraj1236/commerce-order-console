from fastapi import status

from app.core.schemas import ErrorDetail


class AppError(Exception):
    """Base class for expected business errors that map to a specific HTTP response."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    code: str = "bad_request"

    def __init__(self, message: str, details: list[ErrorDetail] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"


class InsufficientStockError(ConflictError):
    code = "insufficient_stock"


class InvalidStatusTransitionError(ConflictError):
    code = "invalid_status_transition"


class OrderAlreadyCancelledError(ConflictError):
    code = "order_already_cancelled"
