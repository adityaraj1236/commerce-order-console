import logging
import math
import secrets
import string
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import InsufficientStockError, NotFoundError
from app.core.logging import log_with_context
from app.core.schemas import ErrorDetail
from app.orders import crud
from app.orders.models import Order, OrderItem, OrderStatus
from app.orders.schemas import (
    OrderCreate,
    OrderItemCreate,
    OrderListResponse,
    OrderRead,
    OrderSummary,
)
from app.products import crud as product_crud
from app.products.models import Product

logger = logging.getLogger(__name__)

_REFERENCE_ALPHABET = string.ascii_uppercase + string.digits


def generate_order_reference() -> str:
    """e.g. ORD-20261125-7K3Q9X: readable over the phone, random suffix from `secrets`."""
    suffix = "".join(secrets.choice(_REFERENCE_ALPHABET) for _ in range(6))
    return f"ORD-{datetime.now(UTC):%Y%m%d}-{suffix}"


def create_order(session: Session, payload: OrderCreate) -> OrderRead:
    """Place an order atomically.

    Stock check, stock deduction and order insert all happen in one transaction while the
    product rows are locked. Any error rolls everything back: no stock change, no order.
    """
    with session.begin():
        locked_products = product_crud.lock_products_by_ids(
            session, [item.product_id for item in payload.items]
        )
        products_by_id = {product.id: product for product in locked_products}

        _ensure_all_products_exist(payload.items, products_by_id)
        _ensure_sufficient_stock(payload.items, products_by_id)

        stock_changes = _deduct_stock(payload.items, products_by_id)
        order = crud.add_order(session, _build_order(payload.items, products_by_id))

    # Logged only after the commit succeeded, so we never report a change that rolled back.
    log_with_context(
        logger,
        "INFO",
        "INVENTORY: Stock deducted (service.py create_order)",
        context={"order_reference": order.order_reference, "changes": stock_changes},
    )
    log_with_context(
        logger,
        "INFO",
        "ORDERS: Order created (service.py create_order)",
        context={
            "order_reference": order.order_reference,
            "total_amount": order.total_amount,
            "line_count": len(order.items),
        },
    )
    return OrderRead.model_validate(order)


def get_order(session: Session, order_id: uuid.UUID) -> OrderRead:
    order = crud.get_order(session, order_id)
    if order is None:
        raise NotFoundError(f"Order '{order_id}' was not found.")
    log_with_context(
        logger,
        "INFO",
        "ORDERS: Order fetched (service.py get_order)",
        context={"order_reference": order.order_reference},
    )
    return OrderRead.model_validate(order)


def get_order_by_reference(session: Session, order_reference: str) -> OrderRead:
    """References are stored uppercase; accept what staff type over the phone ('ord-…', spaces)."""
    normalized_reference = order_reference.strip().upper()
    order = crud.get_order_by_reference(session, normalized_reference)
    if order is None:
        raise NotFoundError(f"Order '{normalized_reference}' was not found.")
    log_with_context(
        logger,
        "INFO",
        "ORDERS: Order fetched by reference (service.py get_order_by_reference)",
        context={"order_reference": order.order_reference},
    )
    return OrderRead.model_validate(order)


def list_orders(
    session: Session,
    *,
    reference: str | None,
    status: OrderStatus | None,
    page: int,
    page_size: int,
) -> OrderListResponse:
    reference = reference.strip() if reference else None
    total = crud.count_orders(session, reference=reference, status=status)
    rows = crud.list_orders(
        session,
        reference=reference,
        status=status,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    items = [
        OrderSummary(
            id=order.id,
            order_reference=order.order_reference,
            status=order.status,
            total_amount=order.total_amount,
            item_count=item_count,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )
        for order, item_count in rows
    ]
    log_with_context(
        logger,
        "INFO",
        "ORDERS: Orders listed (service.py list_orders)",
        context={
            "reference": reference,
            "status": status,
            "page": page,
            "returned": len(items),
            "total": total,
        },
    )
    return OrderListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=math.ceil(total / page_size),
    )


def _ensure_all_products_exist(
    items: list[OrderItemCreate], products_by_id: dict[uuid.UUID, Product]
) -> None:
    missing = [
        (index, item) for index, item in enumerate(items) if item.product_id not in products_by_id
    ]
    if not missing:
        return
    details = [
        ErrorDetail(
            field=f"items.{index}.product_id",
            message=f"Product '{item.product_id}' was not found.",
        )
        for index, item in missing
    ]
    message = (
        details[0].message if len(details) == 1 else f"{len(details)} products were not found."
    )
    raise NotFoundError(message, details)


def _ensure_sufficient_stock(
    items: list[OrderItemCreate], products_by_id: dict[uuid.UUID, Product]
) -> None:
    """Collect every short line, so staff can fix the whole order in one go."""
    details = [
        ErrorDetail(
            field=f"items.{index}.quantity",
            message=(
                f"{product.name}: requested {item.quantity}, available {product.stock_quantity}."
            ),
        )
        for index, item in enumerate(items)
        if item.quantity > (product := products_by_id[item.product_id]).stock_quantity
    ]
    if not details:
        return
    message = (
        f"Insufficient stock. {details[0].message}"
        if len(details) == 1
        else f"Insufficient stock for {len(details)} products."
    )
    raise InsufficientStockError(message, details)


def _deduct_stock(
    items: list[OrderItemCreate], products_by_id: dict[uuid.UUID, Product]
) -> list[dict[str, object]]:
    changes: list[dict[str, object]] = []
    for item in items:
        product = products_by_id[item.product_id]
        before = product.stock_quantity
        product.stock_quantity = before - item.quantity
        changes.append({"sku": product.sku, "before": before, "after": product.stock_quantity})
    return changes


def _build_order(items: list[OrderItemCreate], products_by_id: dict[uuid.UUID, Product]) -> Order:
    """Prices come from the locked catalogue rows and are snapshotted onto each line."""
    order_items = [
        OrderItem(
            product_id=product.id,
            product_name=product.name,
            unit_price=product.price,
            quantity=item.quantity,
            line_total=product.price * item.quantity,
        )
        for item in items
        for product in [products_by_id[item.product_id]]
    ]
    return Order(
        order_reference=generate_order_reference(),
        status=OrderStatus.PLACED,
        total_amount=sum((line.line_total for line in order_items), Decimal("0.00")),
        items=order_items,
    )
