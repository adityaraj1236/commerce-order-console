import threading
import time
import uuid
from collections.abc import Callable
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import ConflictError
from app.db.session import SessionLocal
from app.orders import fulfilment_service
from app.orders.models import OrderStatus
from app.products.models import Product

ORDERS_URL = "/api/v1/orders"

CreateProduct = Callable[..., Product]
StockOf = Callable[[Product], int]
PlaceOrder = Callable[..., dict[str, Any]]


@pytest.fixture
def place_order(client: TestClient) -> PlaceOrder:
    def _place(*lines: tuple[Product, int]) -> dict[str, Any]:
        body = {"items": [{"product_id": str(p.id), "quantity": q} for p, q in lines]}
        response = client.post(ORDERS_URL, json=body)
        assert response.status_code == 201, response.text
        order: dict[str, Any] = response.json()
        return order

    return _place


def _change_status(client: TestClient, order_id: str, status: str) -> Any:
    return client.patch(f"{ORDERS_URL}/{order_id}/status", json={"status": status})


def _move_to(client: TestClient, order_id: str, *statuses: str) -> None:
    for status in statuses:
        assert _change_status(client, order_id, status).status_code == 200


def _current_status(client: TestClient, order_id: str) -> str:
    status: str = client.get(f"{ORDERS_URL}/{order_id}").json()["status"]
    return status


# ---------------------------------------------------------------- valid fulfilment


def test_placed_order_can_be_packed(
    client: TestClient, create_product: CreateProduct, place_order: PlaceOrder
) -> None:
    order = place_order((create_product(), 1))

    response = _change_status(client, order["id"], "PACKED")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "PACKED"
    assert body["allowed_transitions"] == ["SHIPPED", "CANCELLED"]
    assert body["updated_at"] > order["updated_at"]
    assert _current_status(client, order["id"]) == "PACKED"


def test_packed_order_can_be_shipped_and_shipping_does_not_touch_stock(
    client: TestClient, create_product: CreateProduct, place_order: PlaceOrder, stock_of: StockOf
) -> None:
    product = create_product(stock_quantity=5)
    order = place_order((product, 2))
    _move_to(client, order["id"], "PACKED")

    response = _change_status(client, order["id"], "SHIPPED")

    assert response.status_code == 200
    assert response.json()["status"] == "SHIPPED"
    assert response.json()["allowed_transitions"] == []
    assert stock_of(product) == 3


def test_new_order_exposes_its_allowed_transitions(
    create_product: CreateProduct, place_order: PlaceOrder
) -> None:
    order = place_order((create_product(), 1))

    assert order["allowed_transitions"] == ["PACKED", "CANCELLED"]


# ---------------------------------------------------------------- cancellation


def test_cancelling_a_placed_order_restores_stock(
    client: TestClient, create_product: CreateProduct, place_order: PlaceOrder, stock_of: StockOf
) -> None:
    product = create_product(stock_quantity=5)
    order = place_order((product, 2))

    response = _change_status(client, order["id"], "CANCELLED")

    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"
    assert response.json()["allowed_transitions"] == []
    assert stock_of(product) == 5


def test_cancelling_a_packed_order_restores_stock(
    client: TestClient, create_product: CreateProduct, place_order: PlaceOrder, stock_of: StockOf
) -> None:
    product = create_product(stock_quantity=5)
    order = place_order((product, 2))
    _move_to(client, order["id"], "PACKED")

    response = _change_status(client, order["id"], "CANCELLED")

    assert response.status_code == 200
    assert stock_of(product) == 5


def test_cancelling_a_multi_item_order_restores_every_product(
    client: TestClient, create_product: CreateProduct, place_order: PlaceOrder, stock_of: StockOf
) -> None:
    keyboard = create_product(stock_quantity=10)
    mouse = create_product(stock_quantity=4)
    order = place_order((keyboard, 3), (mouse, 4))
    assert (stock_of(keyboard), stock_of(mouse)) == (7, 0)

    _change_status(client, order["id"], "CANCELLED")

    assert (stock_of(keyboard), stock_of(mouse)) == (10, 4)


def test_brief_acceptance_example_restores_stock_exactly_once(
    client: TestClient, create_product: CreateProduct, place_order: PlaceOrder, stock_of: StockOf
) -> None:
    """Place 2 of A (stock 5), cancel: stock 5. Cancelling again must not increase it."""
    product_a = create_product(name="Product A", stock_quantity=5)
    order = place_order((product_a, 2))
    assert stock_of(product_a) == 3

    first = _change_status(client, order["id"], "CANCELLED")
    second = _change_status(client, order["id"], "CANCELLED")

    assert first.status_code == 200
    assert stock_of(product_a) == 5
    assert second.status_code == 409
    error = second.json()["error"]
    assert error["code"] == "order_already_cancelled"
    assert error["message"] == (
        f"Order {order['order_reference']} is already cancelled. Stock was not changed."
    )
    assert stock_of(product_a) == 5


def test_cancelled_order_keeps_its_price_snapshot(
    client: TestClient, create_product: CreateProduct, place_order: PlaceOrder
) -> None:
    order = place_order((create_product(price=Decimal("4499.00")), 2))

    cancelled = _change_status(client, order["id"], "CANCELLED").json()

    assert cancelled["total_amount"] == "8998.00"
    assert cancelled["items"] == order["items"]


# ---------------------------------------------------------------- invalid transitions


@pytest.mark.parametrize(
    ("path_to_current", "target", "expected_hint"),
    [
        ((), "SHIPPED", "Allowed next: PACKED, CANCELLED."),
        ((), "PLACED", "Allowed next: PACKED, CANCELLED."),
        (("PACKED",), "PACKED", "Allowed next: SHIPPED, CANCELLED."),
        (("PACKED",), "PLACED", "Allowed next: SHIPPED, CANCELLED."),
        (("PACKED", "SHIPPED"), "CANCELLED", "SHIPPED is a final status"),
        (("PACKED", "SHIPPED"), "PACKED", "SHIPPED is a final status"),
        (("PACKED", "SHIPPED"), "PLACED", "SHIPPED is a final status"),
        (("CANCELLED",), "PLACED", "CANCELLED is a final status"),
        (("CANCELLED",), "PACKED", "CANCELLED is a final status"),
        (("CANCELLED",), "SHIPPED", "CANCELLED is a final status"),
    ],
)
def test_invalid_transition_is_rejected_and_nothing_changes(
    client: TestClient,
    create_product: CreateProduct,
    place_order: PlaceOrder,
    stock_of: StockOf,
    path_to_current: tuple[str, ...],
    target: str,
    expected_hint: str,
) -> None:
    product = create_product(stock_quantity=5)
    order = place_order((product, 2))
    _move_to(client, order["id"], *path_to_current)
    status_before = _current_status(client, order["id"])
    stock_before = stock_of(product)

    response = _change_status(client, order["id"], target)

    assert response.status_code == 409
    error = response.json()["error"]
    assert error["code"] == "invalid_status_transition"
    assert f"from {status_before} to {target}" in error["message"]
    assert expected_hint in error["message"]
    assert _current_status(client, order["id"]) == status_before
    assert stock_of(product) == stock_before


# ---------------------------------------------------------------- request validation


@pytest.mark.parametrize(
    "body",
    [
        {"status": "DONE"},
        {"status": "packed"},
        {"status": None},
        {},
        {"status": "PACKED", "restore_stock": True},
    ],
)
def test_invalid_status_payload_is_rejected(
    client: TestClient, create_product: CreateProduct, place_order: PlaceOrder, body: Any
) -> None:
    order = place_order((create_product(), 1))

    response = client.patch(f"{ORDERS_URL}/{order['id']}/status", json=body)

    assert response.status_code == 422
    assert _current_status(client, order["id"]) == "PLACED"


def test_unknown_order_returns_404(client: TestClient) -> None:
    response = _change_status(client, str(uuid.uuid4()), "PACKED")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


# ---------------------------------------------------------------- concurrency


def test_concurrent_cancellations_restore_stock_exactly_once(
    client: TestClient,
    create_product: CreateProduct,
    place_order: PlaceOrder,
    stock_of: StockOf,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Five staff members press Cancel on the same order at the same moment.

    A pause after the status check widens the race window. Without the order row lock all
    five would see PLACED and restore stock five times; with it exactly one succeeds.
    """
    original_restore_stock = fulfilment_service._restore_stock

    def slow_restore_stock(*args: Any, **kwargs: Any) -> Any:
        time.sleep(0.3)
        return original_restore_stock(*args, **kwargs)

    monkeypatch.setattr(fulfilment_service, "_restore_stock", slow_restore_stock)

    product = create_product(stock_quantity=5)
    order_id = uuid.UUID(place_order((product, 2))["id"])
    attempts = 5
    start_together = threading.Barrier(attempts)
    outcomes: list[str] = []
    outcomes_lock = threading.Lock()

    def cancel() -> None:
        start_together.wait()
        with SessionLocal() as session:
            try:
                fulfilment_service.update_order_status(session, order_id, OrderStatus.CANCELLED)
                outcome = "cancelled"
            except ConflictError:
                outcome = "rejected"
        with outcomes_lock:
            outcomes.append(outcome)

    threads = [threading.Thread(target=cancel) for _ in range(attempts)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert sorted(outcomes) == ["cancelled"] + ["rejected"] * (attempts - 1)
    assert stock_of(product) == 5
