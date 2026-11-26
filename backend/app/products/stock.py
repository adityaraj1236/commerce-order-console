"""Stock level classification: the single definition of in / low / out of stock.

The dashboard's SQL counts (app/dashboard/crud.py) use the same boundaries:
0 is out of stock, 1..threshold is low stock, above the threshold is in stock.
"""

from enum import StrEnum


class StockLevel(StrEnum):
    IN_STOCK = "in_stock"
    LOW_STOCK = "low_stock"
    OUT_OF_STOCK = "out_of_stock"


def classify_stock(quantity: int, low_stock_threshold: int) -> StockLevel:
    if quantity <= 0:
        return StockLevel.OUT_OF_STOCK
    if quantity <= low_stock_threshold:
        return StockLevel.LOW_STOCK
    return StockLevel.IN_STOCK
