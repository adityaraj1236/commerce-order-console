import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, computed_field

from app.core.config import get_settings
from app.products.stock import StockLevel, classify_stock


class ProductRead(BaseModel):
    """Product as returned by the API. Prices serialize as strings to preserve precision."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    sku: str
    description: str
    price: Decimal
    stock_quantity: int
    created_at: datetime
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_in_stock(self) -> bool:
        return self.stock_quantity > 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def stock_level(self) -> StockLevel:
        """in_stock / low_stock / out_of_stock, using the configured low-stock threshold."""
        return classify_stock(self.stock_quantity, get_settings().low_stock_threshold)


class ProductListResponse(BaseModel):
    items: list[ProductRead]
    total: int
