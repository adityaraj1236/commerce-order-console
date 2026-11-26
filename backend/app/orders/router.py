import uuid
from typing import Annotated

from fastapi import APIRouter, Path, Query
from fastapi import status as http_status

from app.core.schemas import error_responses
from app.db.session import DbSession
from app.orders import fulfilment_service, service
from app.orders.models import OrderStatus
from app.orders.schemas import OrderCreate, OrderListResponse, OrderRead, OrderStatusUpdate

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post(
    "",
    response_model=OrderRead,
    status_code=http_status.HTTP_201_CREATED,
    summary="Place an order",
    responses=error_responses(404, 409, 422),
)
def create_order(payload: OrderCreate, session: DbSession) -> OrderRead:
    return service.create_order(session, payload)


@router.get(
    "",
    response_model=OrderListResponse,
    summary="List orders with reference search, status filter and pagination",
    responses=error_responses(422),
)
def list_orders(
    session: DbSession,
    reference: Annotated[
        str | None,
        Query(max_length=32, description="Partial, case-insensitive order reference"),
    ] = None,
    status: Annotated[OrderStatus | None, Query(description="Only orders in this status")] = None,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=100)] = 20,
) -> OrderListResponse:
    return service.list_orders(
        session, reference=reference, status=status, page=page, page_size=page_size
    )


@router.get(
    "/reference/{order_reference}",
    response_model=OrderRead,
    summary="Get an order by its reference (case-insensitive, exact match)",
    responses=error_responses(404, 422),
)
def get_order_by_reference(
    order_reference: Annotated[str, Path(min_length=1, max_length=32)],
    session: DbSession,
) -> OrderRead:
    return service.get_order_by_reference(session, order_reference)


@router.get(
    "/{order_id}",
    response_model=OrderRead,
    summary="Get an order with all its items",
    responses=error_responses(404, 422),
)
def get_order(order_id: uuid.UUID, session: DbSession) -> OrderRead:
    return service.get_order(session, order_id)


@router.patch(
    "/{order_id}/status",
    response_model=OrderRead,
    summary="Change an order's fulfilment status (cancelling restores stock exactly once)",
    responses=error_responses(404, 409, 422),
)
def update_order_status(
    order_id: uuid.UUID, payload: OrderStatusUpdate, session: DbSession
) -> OrderRead:
    return fulfilment_service.update_order_status(session, order_id, payload.status)
