from collections.abc import Callable, Iterator
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text

from app.db.session import SessionLocal, engine
from app.main import app
from app.orders.models import Order
from app.products.models import Product

BACKEND_DIR = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session", autouse=True)
def migrated_database() -> Iterator[None]:
    """Build the test schema from the real Alembic migrations once per test session."""
    alembic_config = Config(str(BACKEND_DIR / "alembic.ini"))
    alembic_config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    command.downgrade(alembic_config, "base")
    command.upgrade(alembic_config, "head")
    yield
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_tables() -> None:
    """Start every test from empty tables so tests never depend on execution order."""
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE order_items, orders, products RESTART IDENTITY CASCADE"))


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def create_product() -> Callable[..., Product]:
    counter = 0

    def _create(**overrides: Any) -> Product:
        nonlocal counter
        counter += 1
        values: dict[str, Any] = {
            "name": f"Test Product {counter}",
            "sku": f"TEST-{counter:03d}",
            "description": "Test product",
            "price": Decimal("100.00"),
            "stock_quantity": 10,
        }
        values.update(overrides)
        with SessionLocal() as session, session.begin():
            product = Product(**values)
            session.add(product)
        return product

    return _create


@pytest.fixture
def stock_of() -> Callable[[Product], int]:
    """Read a product's stock straight from the database, bypassing any session cache."""

    def _stock_of(product: Product) -> int:
        with SessionLocal() as session:
            stock = session.scalar(select(Product.stock_quantity).where(Product.id == product.id))
        assert stock is not None
        return stock

    return _stock_of


@pytest.fixture
def order_count() -> Callable[[], int]:
    def _order_count() -> int:
        with SessionLocal() as session:
            return session.scalar(select(func.count()).select_from(Order)) or 0

    return _order_count
