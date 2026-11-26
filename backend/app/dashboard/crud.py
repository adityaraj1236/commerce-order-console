"""Aggregate queries for the dashboard. Counting happens in PostgreSQL, never in Python."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.orders.models import Order, OrderStatus
from app.products.models import Product


def count_orders_by_status(session: Session) -> dict[OrderStatus, int]:
    """SELECT status, COUNT(*) FROM orders GROUP BY status. Missing statuses are absent."""
    statement = select(Order.status, func.count()).group_by(Order.status)
    return {status: count for status, count in session.execute(statement).all()}


def count_products_by_stock_level(
    session: Session, low_stock_threshold: int
) -> tuple[int, int, int]:
    """Returns (total, low_stock, out_of_stock) in a single query using filtered counts."""
    statement = select(
        func.count(),
        func.count().filter(Product.stock_quantity.between(1, low_stock_threshold)),
        func.count().filter(Product.stock_quantity == 0),
    ).select_from(Product)
    total, low_stock, out_of_stock = session.execute(statement).one()
    return total, low_stock, out_of_stock
