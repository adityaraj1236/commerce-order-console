import uuid
from collections.abc import Callable
from decimal import Decimal

from fastapi.testclient import TestClient

from app.products.models import Product

PRODUCTS_URL = "/api/v1/products"


def test_list_products_returns_empty_list_when_catalogue_is_empty(client: TestClient) -> None:
    response = client.get(PRODUCTS_URL)

    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}


def test_list_products_returns_all_fields(
    client: TestClient, create_product: Callable[..., Product]
) -> None:
    product = create_product(
        name="Mechanical Keyboard",
        sku="KB-001",
        description="Tenkeyless keyboard",
        price=Decimal("4499.00"),
        stock_quantity=25,
    )

    response = client.get(PRODUCTS_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    item = body["items"][0]
    assert item["id"] == str(product.id)
    assert item["name"] == "Mechanical Keyboard"
    assert item["sku"] == "KB-001"
    assert item["description"] == "Tenkeyless keyboard"
    assert item["stock_quantity"] == 25
    assert item["is_in_stock"] is True
    assert item["created_at"] is not None
    assert item["updated_at"] is not None


def test_list_products_serializes_price_as_exact_decimal_string(
    client: TestClient, create_product: Callable[..., Product]
) -> None:
    create_product(price=Decimal("18999.90"))

    item = client.get(PRODUCTS_URL).json()["items"][0]

    assert item["price"] == "18999.90"


def test_list_products_flags_out_of_stock_products(
    client: TestClient, create_product: Callable[..., Product]
) -> None:
    create_product(name="Available", stock_quantity=3)
    create_product(name="Sold Out", stock_quantity=0)

    items = {item["name"]: item for item in client.get(PRODUCTS_URL).json()["items"]}

    assert items["Available"]["is_in_stock"] is True
    assert items["Sold Out"]["is_in_stock"] is False
    assert items["Sold Out"]["stock_quantity"] == 0
    assert items["Available"]["stock_level"] == "low_stock"
    assert items["Sold Out"]["stock_level"] == "out_of_stock"


def test_list_products_is_sorted_by_name(
    client: TestClient, create_product: Callable[..., Product]
) -> None:
    for name in ["Webcam", "Cable", "Monitor"]:
        create_product(name=name)

    names = [item["name"] for item in client.get(PRODUCTS_URL).json()["items"]]

    assert names == ["Cable", "Monitor", "Webcam"]
    assert client.get(PRODUCTS_URL).json()["total"] == 3


def test_get_product_returns_the_product(
    client: TestClient, create_product: Callable[..., Product]
) -> None:
    product = create_product(name="Webcam", sku="CAM-001", price=Decimal("2799.00"))

    response = client.get(f"{PRODUCTS_URL}/{product.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == str(product.id)
    assert body["name"] == "Webcam"
    assert body["sku"] == "CAM-001"
    assert body["price"] == "2799.00"
    assert body["is_in_stock"] is True


def test_get_product_returns_404_for_unknown_id(client: TestClient) -> None:
    missing_id = uuid.uuid4()

    response = client.get(f"{PRODUCTS_URL}/{missing_id}")

    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "not_found",
        "message": f"Product '{missing_id}' was not found.",
        "details": None,
    }


def test_get_product_returns_422_for_malformed_id(client: TestClient) -> None:
    response = client.get(f"{PRODUCTS_URL}/not-a-uuid")

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"][0]["field"] == "path.product_id"


def test_unknown_route_returns_consistent_error_shape(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json() == {
        "error": {"code": "not_found", "message": "Not Found", "details": None}
    }
