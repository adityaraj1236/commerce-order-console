import uuid

from fastapi import APIRouter

from app.core.schemas import error_responses
from app.db.session import DbSession
from app.products import service
from app.products.schemas import ProductListResponse, ProductRead

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductListResponse, summary="List all products")
def list_products(session: DbSession) -> ProductListResponse:
    return service.list_products(session)


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    summary="Get a product by ID",
    responses=error_responses(404, 422),
)
def get_product(product_id: uuid.UUID, session: DbSession) -> ProductRead:
    return service.get_product(session, product_id)
