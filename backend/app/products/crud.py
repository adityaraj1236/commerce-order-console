"""Database queries for products. Never commits; transactions belong to the service layer."""

import uuid
from collections.abc import Collection, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.products.models import Product


def list_products(session: Session) -> Sequence[Product]:
    statement = select(Product).order_by(Product.name, Product.sku)
    return session.scalars(statement).all()


def get_product(session: Session, product_id: uuid.UUID) -> Product | None:
    return session.get(Product, product_id)


def lock_products_by_ids(session: Session, product_ids: Collection[uuid.UUID]) -> list[Product]:
    """SELECT ... FOR UPDATE: other transactions wait until ours commits or rolls back.

    Rows are locked in id order so two orders touching the same products can never deadlock.
    Must be called inside a transaction; unknown ids are simply absent from the result.
    """
    statement = (
        select(Product).where(Product.id.in_(product_ids)).order_by(Product.id).with_for_update()
    )
    return list(session.scalars(statement).all())
