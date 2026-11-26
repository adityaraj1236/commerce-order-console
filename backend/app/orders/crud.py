"""Database queries for orders. Never commits; transactions belong to the service layer."""

import uuid

from sqlalchemy import ColumnElement, Select, func, select
from sqlalchemy.orm import Session, selectinload

from app.orders.models import Order, OrderItem, OrderStatus


def add_order(session: Session, order: Order) -> Order:
    """Insert the order and its items, so ids and server defaults are populated."""
    session.add(order)
    session.flush()
    return order


def get_order(session: Session, order_id: uuid.UUID) -> Order | None:
    statement = select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    return session.scalar(statement)


def lock_order(session: Session, order_id: uuid.UUID) -> Order | None:
    """SELECT ... FOR UPDATE on the order row, so concurrent status changes run one at a time.

    Must be called inside a transaction. Items are loaded with a separate, unlocked query;
    they never change after the order is created.
    """
    statement = (
        select(Order)
        .where(Order.id == order_id)
        .options(selectinload(Order.items))
        .with_for_update()
    )
    return session.scalar(statement)


def get_order_by_reference(session: Session, order_reference: str) -> Order | None:
    statement = (
        select(Order)
        .where(Order.order_reference == order_reference)
        .options(selectinload(Order.items))
    )
    return session.scalar(statement)


def _escape_like(value: str) -> str:
    """Treat %, _ and \\ in user input literally inside a LIKE pattern."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _order_filters(reference: str | None, status: OrderStatus | None) -> list[ColumnElement[bool]]:
    filters: list[ColumnElement[bool]] = []
    if reference:
        filters.append(Order.order_reference.ilike(f"%{_escape_like(reference)}%", escape="\\"))
    if status is not None:
        filters.append(Order.status == status)
    return filters


def list_orders(
    session: Session,
    *,
    reference: str | None,
    status: OrderStatus | None,
    limit: int,
    offset: int,
) -> list[tuple[Order, int]]:
    """Newest first. Each row is (order, total units across its lines)."""
    item_count = (
        select(func.coalesce(func.sum(OrderItem.quantity), 0))
        .where(OrderItem.order_id == Order.id)
        .scalar_subquery()
    )
    statement: Select[tuple[Order, int]] = (
        select(Order, item_count)
        .where(*_order_filters(reference, status))
        .order_by(Order.created_at.desc(), Order.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return [(order, count) for order, count in session.execute(statement).all()]


def count_orders(session: Session, *, reference: str | None, status: OrderStatus | None) -> int:
    statement = select(func.count()).select_from(Order).where(*_order_filters(reference, status))
    return session.scalar(statement) or 0
