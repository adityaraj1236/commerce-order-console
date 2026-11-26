import logging
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.core.logging import log_with_context
from app.products import crud
from app.products.schemas import ProductListResponse, ProductRead

logger = logging.getLogger(__name__)


def list_products(session: Session) -> ProductListResponse:
    products = crud.list_products(session)
    items = [ProductRead.model_validate(product) for product in products]
    log_with_context(
        logger,
        "INFO",
        "PRODUCTS: Products listed (service.py list_products)",
        context={"count": len(items)},
    )
    return ProductListResponse(items=items, total=len(items))


def get_product(session: Session, product_id: uuid.UUID) -> ProductRead:
    product = crud.get_product(session, product_id)
    if product is None:
        raise NotFoundError(f"Product '{product_id}' was not found.")
    log_with_context(
        logger,
        "INFO",
        "PRODUCTS: Product fetched (service.py get_product)",
        context={"product_id": product_id},
    )
    return ProductRead.model_validate(product)
