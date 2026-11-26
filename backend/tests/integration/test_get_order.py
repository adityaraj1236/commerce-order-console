import uuid
from collections.abc import Callable
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.products.models import Product

ORDERS_URL = "/api/v1/orders"


@pytest.fixture
def placed_order(client: TestClient, create_product: Callable[..., Product]) -> dict[str, Any]:
    keyboard = create_product(name="Keyboard", price=Decimal("4499.00"), stock_quantity=10)
    mouse = create_product(name="Mouse", price=Decimal("1899.00"), stock_quantity=10)
    body = {
        "items": [
            {"product_id": str(keyboard.id), "quantity": 2},
            {"product_id": str(mouse.id), "quantity": 1},
        ]
    }
    response = client.post(ORDERS_URL, json=body)
    assert response.status_code == 201
    order: dict[str, Any] = response.json()
    return order


# ---------------------------------------------------------------- GET /orders/{order_id}


def test_get_order_returns_full_details(client: TestClient, placed_order: dict[str, Any]) -> None:
    response = client.get(f"{ORDERS_URL}/{placed_order['id']}")

    assert response.status_code == 200
    order = response.json()
    assert order == placed_order
    assert order["total_amount"] == "10897.00"
    assert order["item_count"] == 3
    assert [
        (line["product_name"], line["quantity"], line["line_total"]) for line in order["items"]
    ] == [
        ("Keyboard", 2, "8998.00"),
        ("Mouse", 1, "1899.00"),
    ]


def test_get_order_returns_404_for_unknown_id(client: TestClient) -> None:
    missing_id = uuid.uuid4()

    response = client.get(f"{ORDERS_URL}/{missing_id}")

    assert response.status_code == 404
    assert response.json()["error"]["message"] == f"Order '{missing_id}' was not found."


def test_get_order_returns_422_for_malformed_id(client: TestClient) -> None:
    response = client.get(f"{ORDERS_URL}/not-a-uuid")

    assert response.status_code == 422
    assert response.json()["error"]["details"][0]["field"] == "path.order_id"


# ---------------------------------------------------------------- GET /orders/reference/{ref}


def test_get_order_by_reference_returns_full_details(
    client: TestClient, placed_order: dict[str, Any]
) -> None:
    response = client.get(f"{ORDERS_URL}/reference/{placed_order['order_reference']}")

    assert response.status_code == 200
    assert response.json() == placed_order


@pytest.mark.parametrize("transform", [str.lower, lambda ref: f"  {ref} "])
def test_get_order_by_reference_accepts_lowercase_and_surrounding_spaces(
    client: TestClient, placed_order: dict[str, Any], transform: Callable[[str], str]
) -> None:
    response = client.get(f"{ORDERS_URL}/reference/{transform(placed_order['order_reference'])}")

    assert response.status_code == 200
    assert response.json()["id"] == placed_order["id"]


def test_get_order_by_reference_requires_an_exact_match(
    client: TestClient, placed_order: dict[str, Any]
) -> None:
    partial = placed_order["order_reference"][-6:]

    response = client.get(f"{ORDERS_URL}/reference/{partial}")

    assert response.status_code == 404
    assert response.json()["error"]["message"] == f"Order '{partial}' was not found."


def test_get_order_by_reference_returns_404_for_unknown_reference(client: TestClient) -> None:
    response = client.get(f"{ORDERS_URL}/reference/ORD-20260101-ZZZZZZ")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_get_order_by_reference_rejects_overlong_reference(client: TestClient) -> None:
    response = client.get(f"{ORDERS_URL}/reference/{'X' * 33}")

    assert response.status_code == 422
