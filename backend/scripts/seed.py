"""Seed the product catalogue with synthetic data.

Usage (from the backend directory):
    uv run python -m scripts.seed

Idempotent: products whose SKU already exists are left untouched, so re-running
never duplicates rows or resets stock that real orders have changed.
"""

import logging
from collections import Counter

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.config import get_settings
from app.core.logging import log_with_context, setup_logging
from app.db.session import SessionLocal
from app.products.models import Product
from scripts.seed_data import build_seed_products

logger = logging.getLogger("scripts.seed")

SEED_PRODUCTS = build_seed_products()


def _ensure_unique_skus(products: list[dict[str, object]]) -> None:
    duplicates = [sku for sku, count in Counter(p["sku"] for p in products).items() if count > 1]
    if duplicates:
        raise ValueError(f"Duplicate SKUs in seed data: {duplicates}")


def seed_products() -> int:
    """Insert missing seed products. Returns the number of rows inserted."""
    _ensure_unique_skus(SEED_PRODUCTS)
    with SessionLocal() as session, session.begin():
        statement = (
            insert(Product)
            .values(SEED_PRODUCTS)
            .on_conflict_do_nothing(index_elements=[Product.sku])
            .returning(Product.sku)
        )
        inserted_skus = session.scalars(statement).all()
        total = len(session.scalars(select(Product.id)).all())

    log_with_context(
        logger,
        "INFO",
        "SEED: Seed complete (seed.py seed_products)",
        context={
            "inserted": len(inserted_skus),
            "already_present": len(SEED_PRODUCTS) - len(inserted_skus),
            "total_products": total,
        },
    )
    return len(inserted_skus)


if __name__ == "__main__":
    setup_logging(get_settings().environment)
    seed_products()
