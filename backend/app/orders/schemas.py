import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from app.orders.models import OrderStatus
from app.orders.status_rules import allowed_next_statuses

# Upper bound of PostgreSQL INTEGER, the column type of quantity and stock_quantity.
POSTGRES_INTEGER_MAX = 2_147_483_647

Quantity = Annotated[int, Field(strict=True, ge=1, le=POSTGRES_INTEGER_MAX)]


class OrderItemCreate(BaseModel):
    """One requested line. Prices are deliberately absent: the backend decides them."""

    model_config = ConfigDict(extra="forbid")

    product_id: uuid.UUID
    quantity: Quantity


class OrderCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[OrderItemCreate]

    @field_validator("items")
    @classmethod
    def validate_items(cls, items: list[OrderItemCreate]) -> list[OrderItemCreate]:
        if not items:
            raise ValueError("Order must contain at least one item")
        product_ids = [item.product_id for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise ValueError("Each product can appear only once in an order")
        return items


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    product_id: uuid.UUID
    product_name: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal


class OrderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    order_reference: str
    status: OrderStatus
    total_amount: Decimal
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead]

    @computed_field  # type: ignore[prop-decorator]
    @property
    def item_count(self) -> int:
        """Total units across all lines (2 keyboards + 1 mouse = 3)."""
        return sum(item.quantity for item in self.items)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def allowed_transitions(self) -> list[OrderStatus]:
        """Statuses this order may move to next; the UI shows only these actions."""
        return list(allowed_next_statuses(self.status))


class OrderStatusUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: OrderStatus


class OrderSummary(BaseModel):
    """One row of the order list. item_count is computed in SQL; items are not loaded."""

    id: uuid.UUID
    order_reference: str
    status: OrderStatus
    total_amount: Decimal
    item_count: int
    created_at: datetime
    updated_at: datetime


class OrderListResponse(BaseModel):
    items: list[OrderSummary]
    total: int
    page: int
    page_size: int
    total_pages: int
