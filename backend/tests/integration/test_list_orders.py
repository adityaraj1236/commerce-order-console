from collections.abc import Callable
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.orders.models import Order, OrderStatus
from app.products.models import Product

ORDERS_URL = "/api/v1/orders"

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


def _set_status(order_id: str, status: OrderStatus) -> None:
    """Status transitions have no API yet, so set the state directly for filter tests."""
    with SessionLocal() as session, session.begin():
        order = session.get(Order, order_id)
        assert order is not None
        order.status = status


def test_list_orders_returns_empty_page_when_there_are_no_orders(client: TestClient) -> None:
    response = client.get(ORDERS_URL)

    assert response.status_code == 200
    assert response.json() == {
        "items": [],
        "total": 0,
        "page": 1,
        "page_size": 20,
        "total_pages": 0,
    }


def test_list_orders_returns_summary_fields_newest_first(
    client: TestClient, create_product: Callable[..., Product], place_order: PlaceOrder
) -> None:
    keyboard = create_product(price=Decimal("4499.00"), stock_quantity=10)
    mouse = create_product(price=Decimal("1899.00"), stock_quantity=10)
    first = place_order((keyboard, 1))
    second = place_order((keyboard, 2), (mouse, 3))

    body = client.get(ORDERS_URL).json()

    assert body["total"] == 2
    assert [order["id"] for order in body["items"]] == [second["id"], first["id"]]
    newest = body["items"][0]
    assert newest == {
        "id": second["id"],
        "order_reference": second["order_reference"],
        "status": "PLACED",
        "total_amount": "14695.00",
        "item_count": 5,
        "created_at": second["created_at"],
        "updated_at": second["updated_at"],
    }


def test_list_orders_filters_by_status(
    client: TestClient, create_product: Callable[..., Product], place_order: PlaceOrder
) -> None:
    product = create_product(stock_quantity=10)
    placed = place_order((product, 1))
    packed = place_order((product, 1))
    _set_status(packed["id"], OrderStatus.PACKED)

    packed_only = client.get(ORDERS_URL, params={"status": "PACKED"}).json()
    placed_only = client.get(ORDERS_URL, params={"status": "PLACED"}).json()
    shipped_only = client.get(ORDERS_URL, params={"status": "SHIPPED"}).json()

    assert [order["id"] for order in packed_only["items"]] == [packed["id"]]
    assert [order["id"] for order in placed_only["items"]] == [placed["id"]]
    assert shipped_only["items"] == []
    assert shipped_only["total"] == 0


def test_list_orders_searches_reference_partially_and_case_insensitively(
    client: TestClient, create_product: Callable[..., Product], place_order: PlaceOrder
) -> None:
    product = create_product(stock_quantity=10)
    target = place_order((product, 1))
    place_order((product, 1))
    suffix = target["order_reference"][-6:]

    for search in (suffix, suffix.lower(), target["order_reference"], f"  {suffix}  "):
        body = client.get(ORDERS_URL, params={"reference": search}).json()
        assert [order["id"] for order in body["items"]] == [target["id"]], search


def test_reference_search_treats_wildcards_literally(
    client: TestClient, create_product: Callable[..., Product], place_order: PlaceOrder
) -> None:
    place_order((create_product(stock_quantity=10), 1))

    for wildcard in ("%", "_", "ORD%"):
        body = client.get(ORDERS_URL, params={"reference": wildcard}).json()
        assert body["total"] == 0, wildcard


def test_list_orders_combines_search_and_status_filter(
    client: TestClient, create_product: Callable[..., Product], place_order: PlaceOrder
) -> None:
    product = create_product(stock_quantity=10)
    order = place_order((product, 1))
    suffix = order["order_reference"][-6:]

    matching = client.get(ORDERS_URL, params={"reference": suffix, "status": "PLACED"}).json()
    wrong_status = client.get(ORDERS_URL, params={"reference": suffix, "status": "PACKED"}).json()

    assert matching["total"] == 1
    assert wrong_status["total"] == 0


def test_list_orders_paginates(
    client: TestClient, create_product: Callable[..., Product], place_order: PlaceOrder
) -> None:
    product = create_product(stock_quantity=10)
    created = [place_order((product, 1))["id"] for _ in range(5)]
    newest_first = list(reversed(created))

    pages = [
        client.get(ORDERS_URL, params={"page": page, "page_size": 2}).json()
        for page in (1, 2, 3, 4)
    ]

    assert [[o["id"] for o in page["items"]] for page in pages] == [
        newest_first[0:2],
        newest_first[2:4],
        newest_first[4:5],
        [],
    ]
    assert all(page["total"] == 5 and page["total_pages"] == 3 for page in pages)


@pytest.mark.parametrize(
    "params",
    [
        {"status": "DONE"},
        {"status": "placed"},
        {"page": 0},
        {"page_size": 0},
        {"page_size": 101},
        {"reference": "X" * 33},
    ],
)
def test_list_orders_rejects_invalid_query_parameters(
    client: TestClient, params: dict[str, Any]
) -> None:
    response = client.get(ORDERS_URL, params=params)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"
