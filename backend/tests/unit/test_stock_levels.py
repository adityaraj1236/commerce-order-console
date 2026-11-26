import pytest

from app.products.stock import StockLevel, classify_stock

THRESHOLD = 5


@pytest.mark.parametrize(
    ("quantity", "expected"),
    [
        (0, StockLevel.OUT_OF_STOCK),
        (1, StockLevel.LOW_STOCK),
        (5, StockLevel.LOW_STOCK),
        (6, StockLevel.IN_STOCK),
        (120, StockLevel.IN_STOCK),
    ],
)
def test_classify_stock_boundaries(quantity: int, expected: StockLevel) -> None:
    assert classify_stock(quantity, THRESHOLD) is expected
