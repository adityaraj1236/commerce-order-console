"""Order fulfilment: status transitions and cancellation with stock restoration."""

import logging
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import (
    InvalidStatusTransitionError,
    NotFoundError,
    OrderAlreadyCancelledError,
)
from app.core.logging import log_with_context
from app.orders import crud, status_rules
from app.orders.models import Order, OrderStatus
from app.orders.schemas import OrderRead
from app.products import crud as product_crud

logger = logging.getLogger(__name__)


def update_order_status(session: Session, order_id: uuid.UUID, target: OrderStatus) -> OrderRead:
    """Move an order to `target` if the state machine allows it.

    The order row is locked first, so two simultaneous requests (e.g. two staff members
    pressing Cancel) run one after the other: the second sees the updated status and is
    rejected. Cancelling restores stock in the same transaction as the status change, so
    stock is restored exactly once or not at all.
    """
    with session.begin():
        order = crud.lock_order(session, order_id)
        if order is None:
            raise NotFoundError(f"Order '{order_id}' was not found.")

        previous = order.status
        _ensure_transition_allowed(order, target)

        stock_changes = _restore_stock(session, order) if target == OrderStatus.CANCELLED else []
        order.status = target
        session.flush()

    log_with_context(
        logger,
        "INFO",
        "ORDERS: Order status changed (fulfilment_service.py update_order_status)",
        context={
            "order_reference": order.order_reference,
            "from_status": previous,
            "to_status": target,
        },
    )
    if target == OrderStatus.CANCELLED:
        log_with_context(
            logger,
            "INFO",
            "INVENTORY: Stock restored after cancellation (fulfilment_service.py "
            "update_order_status)",
            context={"order_reference": order.order_reference, "changes": stock_changes},
        )
    return OrderRead.model_validate(order)


def _ensure_transition_allowed(order: Order, target: OrderStatus) -> None:
    current = order.status
    if current == OrderStatus.CANCELLED and target == OrderStatus.CANCELLED:
        raise OrderAlreadyCancelledError(
            f"Order {order.order_reference} is already cancelled. Stock was not changed."
        )
    if status_rules.can_transition(current, target):
        return

    allowed = status_rules.allowed_next_statuses(current)
    hint = (
        f"Allowed next: {', '.join(allowed)}."
        if allowed
        else f"{current} is a final status; no further changes are allowed."
    )
    raise InvalidStatusTransitionError(
        f"Cannot change order {order.order_reference} from {current} to {target}. {hint}"
    )


def _restore_stock(session: Session, order: Order) -> list[dict[str, object]]:
    """Give each line's quantity back to its product. Product rows are locked in id order,
    the same order create_order uses, so the two can never deadlock."""
    quantities = {item.product_id: item.quantity for item in order.items}
    changes: list[dict[str, object]] = []
    for product in product_crud.lock_products_by_ids(session, quantities.keys()):
        before = product.stock_quantity
        product.stock_quantity = before + quantities[product.id]
        changes.append({"sku": product.sku, "before": before, "after": product.stock_quantity})
    return changes
