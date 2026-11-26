from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.error_handlers import register_exception_handlers
from app.core.exceptions import ConflictError, NotFoundError


def _build_app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/not-found")
    def raise_not_found() -> None:
        raise NotFoundError("Product not found.")

    @app.get("/conflict")
    def raise_conflict() -> None:
        raise ConflictError("Insufficient stock.")

    @app.get("/boom")
    def raise_unexpected() -> None:
        raise RuntimeError("database password is hunter2")

    @app.get("/items/{item_id}")
    def read_item(item_id: int) -> dict[str, int]:
        return {"item_id": item_id}

    return app


client = TestClient(_build_app(), raise_server_exceptions=False)


def test_not_found_error_maps_to_404() -> None:
    response = client.get("/not-found")

    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "not_found",
        "message": "Product not found.",
        "details": None,
    }


def test_conflict_error_maps_to_409() -> None:
    response = client.get("/conflict")

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_unexpected_error_returns_500_without_leaking_internals() -> None:
    response = client.get("/boom")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "hunter2" not in response.text


def test_validation_error_returns_422_with_field_details() -> None:
    response = client.get("/items/not-a-number")

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"][0]["field"] == "path.item_id"
