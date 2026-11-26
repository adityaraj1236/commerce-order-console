"""Imports every ORM model so they are registered on Base.metadata.

Alembic autogenerate imports this module; add each new feature's models here.
"""

from app.orders.models import Order, OrderItem, OrderStatus
from app.products.models import Product

__all__ = ["Order", "OrderItem", "OrderStatus", "Product"]
