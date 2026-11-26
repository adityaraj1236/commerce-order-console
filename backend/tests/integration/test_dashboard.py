from collections.abc import Callable
from typing import Any

from fastapi.testclient import TestClient

from app.products.models import Product

SUMMARY_URL = "/api/v1/dashboard/summary"
ORDERS_URL = "/api/v1/orders"


def _place_order(client: TestClient, product: Product) -> dict[str, Any]:
    body = {"items": [{"product_id": str(product.id), "quantity": 1}]}
    response = client.post(ORDERS_URL, json=body)
    assert response.status_code == 201
    order: dict[str, Any] = response.json()
    return order


def _change_status(client: TestClient, order_id: str, *statuses: str) -> None:
    for status in statuses:
        response = client.patch(f"{ORDERS_URL}/{order_id}/status", json={"status": status})
        assert response.status_code == 200


def test_summary_is_all_zeros_on_an_empty_database(client: TestClient) -> None:
    response = client.get(SUMMARY_URL)

    assert response.status_code == 200
    assert response.json() == {
        "orders": {
            "total": 0,
            "by_status": {"PLACED": 0, "PACKED": 0, "SHIPPED": 0, "CANCELLED": 0},
        },
        "products": {
            "total": 0,
            "low_stock": 0,
            "out_of_stock": 0,
            "low_stock_threshold": 5,
        },
    }


def test_summary_counts_orders_by_status(
    client: TestClient, create_product: Callable[..., Product]
) -> None:
    product = create_product(stock_quantity=100)
    orders = [_place_order(client, product)["id"] for _ in range(6)]
    _change_status(client, orders[1], "PACKED")
    _change_status(client, orders[2], "PACKED")
    _change_status(client, orders[3], "PACKED", "SHIPPED")
    _change_status(client, orders[4], "CANCELLED")
    _change_status(client, orders[5], "PACKED", "CANCELLED")

    stats = client.get(SUMMARY_URL).json()["orders"]

    assert stats == {
        "total": 6,
        "by_status": {"PLACED": 1, "PACKED": 2, "SHIPPED": 1, "CANCELLED": 2},
    }


def test_summary_classifies_stock_levels_at_the_threshold_boundaries(
    client: TestClient, create_product: Callable[..., Product]
) -> None:
    for stock in (0, 0, 1, 5, 6, 120):
        create_product(stock_quantity=stock)

    stats = client.get(SUMMARY_URL).json()["products"]

    assert stats == {
        "total": 6,
        "low_stock": 2,  # 1 and 5; 6 is above the threshold
        "out_of_stock": 2,  # 0 is counted separately, not as low stock
        "low_stock_threshold": 5,
    }


def test_summary_reflects_stock_changes_from_orders(
    client: TestClient, create_product: Callable[..., Product]
) -> None:
    product = create_product(stock_quantity=6)
    body = {"items": [{"product_id": str(product.id), "quantity": 6}]}
    order = client.post(ORDERS_URL, json=body).json()

    after_order = client.get(SUMMARY_URL).json()["products"]
    _change_status(client, order["id"], "CANCELLED")
    after_cancel = client.get(SUMMARY_URL).json()["products"]

    assert (after_order["low_stock"], after_order["out_of_stock"]) == (0, 1)
    assert (after_cancel["low_stock"], after_cancel["out_of_stock"]) == (0, 0)
