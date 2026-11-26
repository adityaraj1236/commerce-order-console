from typing import Any

from fastapi.testclient import TestClient

ERROR_RESPONSE_REF = "#/components/schemas/ErrorResponse"


def _response_schema_ref(openapi: dict[str, Any], path: str, status_code: str) -> str:
    response = openapi["paths"][path]["get"]["responses"][status_code]
    return response["content"]["application/json"]["schema"]["$ref"]


def test_get_product_documents_404_and_422_with_our_error_shape(client: TestClient) -> None:
    openapi = client.get("/openapi.json").json()
    path = "/api/v1/products/{product_id}"

    assert _response_schema_ref(openapi, path, "404") == ERROR_RESPONSE_REF
    assert _response_schema_ref(openapi, path, "422") == ERROR_RESPONSE_REF


def test_error_response_schema_matches_the_runtime_error_body(client: TestClient) -> None:
    openapi = client.get("/openapi.json").json()
    schemas = openapi["components"]["schemas"]

    assert set(schemas["ErrorResponse"]["properties"]) == {"error"}
    assert set(schemas["ErrorBody"]["properties"]) == {"code", "message", "details"}
    assert set(schemas["ErrorDetail"]["properties"]) == {"field", "message"}
