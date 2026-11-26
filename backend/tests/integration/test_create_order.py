import re
import threading
import time
import uuid
from collections.abc import Callable
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update

from app.core.exceptions import InsufficientStockError
from app.db.session import SessionLocal
from app.orders import service
from app.orders.models import OrderItem
from app.orders.schemas import POSTGRES_INTEGER_MAX, OrderCreate
from app.products.models import Product

ORDERS_URL = "/api/v1/orders"

CreateProduct = Callable[..., Product]
StockOf = Callable[[Product], int]
OrderCount = Callable[[], int]


def _order_body(*lines: tuple[Product | uuid.UUID, Any]) -> dict[str, Any]:
    return {
        "items": [
            {
                "product_id": str(target.id if isinstance(target, Product) else target),
                "quantity": quantity,
            }
            for target, quantity in lines
        ]
    }


# ---------------------------------------------------------------- successful placement


def test_single_product_order_is_created_and_stock_deducted(
    client: TestClient, create_product: CreateProduct, stock_of: StockOf
) -> None:
    keyboard = create_product(name="Keyboard", price=Decimal("4499.00"), stock_quantity=5)

    response = client.post(ORDERS_URL, json=_order_body((keyboard, 2)))

    assert response.status_code == 201
    order = response.json()
    assert order["status"] == "PLACED"
    assert order["total_amount"] == "8998.00"
    assert order["item_count"] == 2
    assert re.fullmatch(r"ORD-\d{8}-[A-Z0-9]{6}", order["order_reference"])
    assert order["created_at"] is not None
    assert order["items"] == [
        {
            "product_id": str(keyboard.id),
            "product_name": "Keyboard",
            "unit_price": "4499.00",
            "quantity": 2,
            "line_total": "8998.00",
        }
    ]
    assert stock_of(keyboard) == 3


def test_multi_product_order_calculates_line_totals_and_grand_total(
    client: TestClient, create_product: CreateProduct, stock_of: StockOf
) -> None:
    keyboard = create_product(name="Keyboard", price=Decimal("4499.00"), stock_quantity=10)
    mouse = create_product(name="Mouse", price=Decimal("1899.50"), stock_quantity=10)

    response = client.post(ORDERS_URL, json=_order_body((keyboard, 2), (mouse, 3)))

    assert response.status_code == 201
    order = response.json()
    lines = {line["product_name"]: line for line in order["items"]}
    assert lines["Keyboard"]["line_total"] == "8998.00"
    assert lines["Mouse"]["line_total"] == "5698.50"
    assert order["total_amount"] == "14696.50"
    assert order["item_count"] == 5
    assert stock_of(keyboard) == 8
    assert stock_of(mouse) == 7


def test_order_can_take_the_last_unit_in_stock(
    client: TestClient, create_product: CreateProduct, stock_of: StockOf
) -> None:
    stand = create_product(stock_quantity=2)

    response = client.post(ORDERS_URL, json=_order_body((stand, 2)))

    assert response.status_code == 201
    assert stock_of(stand) == 0


def test_unit_price_is_a_snapshot_unaffected_by_later_price_changes(
    client: TestClient, create_product: CreateProduct
) -> None:
    keyboard = create_product(price=Decimal("4499.00"), stock_quantity=5)
    order_id = client.post(ORDERS_URL, json=_order_body((keyboard, 1))).json()["id"]

    with SessionLocal() as session, session.begin():
        session.execute(
            update(Product).where(Product.id == keyboard.id).values(price=Decimal("9999.00"))
        )

    with SessionLocal() as session:
        stored_price = session.scalar(
            select(OrderItem.unit_price).where(OrderItem.order_id == uuid.UUID(order_id))
        )
    assert stored_price == Decimal("4499.00")


# ---------------------------------------------------------------- insufficient stock


def test_brief_acceptance_example_rejects_whole_order_and_keeps_stock(
    client: TestClient,
    create_product: CreateProduct,
    stock_of: StockOf,
    order_count: OrderCount,
) -> None:
    """A has 5, B has 0. Ordering 2xA + 1xB fails; A still has 5 and no order exists."""
    product_a = create_product(name="Product A", stock_quantity=5)
    product_b = create_product(name="Product B", stock_quantity=0)

    response = client.post(ORDERS_URL, json=_order_body((product_a, 2), (product_b, 1)))

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "insufficient_stock"
    assert error["details"] == [
        {"field": "items.1.quantity", "message": "Product B: requested 1, available 0."}
    ]
    assert stock_of(product_a) == 5
    assert stock_of(product_b) == 0
    assert order_count() == 0


def test_insufficient_stock_reports_every_short_line(
    client: TestClient, create_product: CreateProduct
) -> None:
    monitor = create_product(name="Monitor", stock_quantity=1)
    hub = create_product(name="Hub", stock_quantity=3)
    cable = create_product(name="Cable", stock_quantity=100)

    response = client.post(ORDERS_URL, json=_order_body((monitor, 2), (cable, 1), (hub, 4)))

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["message"] == "Insufficient stock for 2 products."
    assert [detail["field"] for detail in error["details"]] == [
        "items.0.quantity",
        "items.2.quantity",
    ]


# ---------------------------------------------------------------- unknown products


def test_unknown_product_returns_404_and_changes_nothing(
    client: TestClient,
    create_product: CreateProduct,
    stock_of: StockOf,
    order_count: OrderCount,
) -> None:
    keyboard = create_product(stock_quantity=5)
    missing_id = uuid.uuid4()

    response = client.post(ORDERS_URL, json=_order_body((keyboard, 1), (missing_id, 1)))

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "not_found"
    assert error["details"][0]["field"] == "items.1.product_id"
    assert stock_of(keyboard) == 5
    assert order_count() == 0


# ---------------------------------------------------------------- request validation


@pytest.mark.parametrize(
    ("quantity", "reason"),
    [
        (0, "zero"),
        (-1, "negative"),
        (2.5, "fractional"),
        ("2", "string"),
        (True, "boolean"),
        (POSTGRES_INTEGER_MAX + 1, "beyond PostgreSQL INTEGER"),
    ],
)
def test_invalid_quantity_is_rejected(
    client: TestClient,
    create_product: CreateProduct,
    stock_of: StockOf,
    quantity: Any,
    reason: str,
) -> None:
    keyboard = create_product(stock_quantity=5)

    response = client.post(ORDERS_URL, json=_order_body((keyboard, quantity)))

    assert response.status_code == 422, reason
    assert response.json()["error"]["details"][0]["field"] == "body.items.0.quantity"
    assert stock_of(keyboard) == 5


def test_empty_cart_is_rejected(client: TestClient, order_count: OrderCount) -> None:
    response = client.post(ORDERS_URL, json={"items": []})

    assert response.status_code == 422
    assert "at least one item" in response.json()["error"]["details"][0]["message"]
    assert order_count() == 0


def test_duplicate_product_lines_are_rejected(
    client: TestClient, create_product: CreateProduct, stock_of: StockOf
) -> None:
    keyboard = create_product(stock_quantity=5)

    response = client.post(ORDERS_URL, json=_order_body((keyboard, 2), (keyboard, 1)))

    assert response.status_code == 422
    assert "only once" in response.json()["error"]["details"][0]["message"]
    assert stock_of(keyboard) == 5


def test_client_supplied_prices_are_rejected(
    client: TestClient, create_product: CreateProduct
) -> None:
    keyboard = create_product(stock_quantity=5)
    body = _order_body((keyboard, 1))
    body["items"][0]["unit_price"] = "1.00"
    body["total_amount"] = "1.00"

    response = client.post(ORDERS_URL, json=body)

    assert response.status_code == 422
    fields = {detail["field"] for detail in response.json()["error"]["details"]}
    assert fields == {"body.items.0.unit_price", "body.total_amount"}


def test_malformed_product_id_is_rejected(client: TestClient) -> None:
    response = client.post(ORDERS_URL, json=_order_body(("not-a-uuid", 1)))  # type: ignore[arg-type]

    assert response.status_code == 422


# ---------------------------------------------------------------- concurrency


def test_concurrent_orders_for_the_last_unit_never_oversell(
    create_product: CreateProduct,
    stock_of: StockOf,
    order_count: OrderCount,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Five staff members try to buy the single remaining unit at the same moment.

    A pause is injected between the stock check and the deduction to widen the race window.
    Without the row lock all five would pass the check and the product would be oversold;
    with the lock the others wait, then see the updated stock and are rejected.
    """
    original_deduct_stock = service._deduct_stock

    def slow_deduct_stock(*args: Any, **kwargs: Any) -> Any:
        time.sleep(0.3)
        return original_deduct_stock(*args, **kwargs)

    monkeypatch.setattr(service, "_deduct_stock", slow_deduct_stock)

    headset = create_product(stock_quantity=1)
    attempts = 5
    start_together = threading.Barrier(attempts)
    outcomes: list[str] = []
    outcomes_lock = threading.Lock()

    def place_order() -> None:
        payload = OrderCreate.model_validate(_order_body((headset, 1)))
        start_together.wait()
        with SessionLocal() as session:
            try:
                service.create_order(session, payload)
                outcome = "created"
            except InsufficientStockError:
                outcome = "rejected"
        with outcomes_lock:
            outcomes.append(outcome)

    threads = [threading.Thread(target=place_order) for _ in range(attempts)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert sorted(outcomes) == ["created"] + ["rejected"] * (attempts - 1)
    assert stock_of(headset) == 0
    assert order_count() == 1
