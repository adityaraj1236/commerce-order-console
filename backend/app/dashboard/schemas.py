from pydantic import BaseModel

from app.orders.models import OrderStatus


class OrderStats(BaseModel):
    total: int
    by_status: dict[OrderStatus, int]


class ProductStats(BaseModel):
    total: int
    low_stock: int
    out_of_stock: int
    low_stock_threshold: int


class DashboardSummary(BaseModel):
    orders: OrderStats
    products: ProductStats
