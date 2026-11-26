import pytest

from app.orders.models import OrderStatus
from app.orders.status_rules import allowed_next_statuses, can_transition

PLACED, PACKED, SHIPPED, CANCELLED = (
    OrderStatus.PLACED,
    OrderStatus.PACKED,
    OrderStatus.SHIPPED,
    OrderStatus.CANCELLED,
)

ALLOWED = {
    (PLACED, PACKED),
    (PACKED, SHIPPED),
    (PLACED, CANCELLED),
    (PACKED, CANCELLED),
}


@pytest.mark.parametrize("current", list(OrderStatus))
@pytest.mark.parametrize("target", list(OrderStatus))
def test_every_transition_matches_the_brief(current: OrderStatus, target: OrderStatus) -> None:
    assert can_transition(current, target) is ((current, target) in ALLOWED)


@pytest.mark.parametrize(
    ("current", "expected"),
    [
        (PLACED, (PACKED, CANCELLED)),
        (PACKED, (SHIPPED, CANCELLED)),
        (SHIPPED, ()),
        (CANCELLED, ()),
    ],
)
def test_allowed_next_statuses(current: OrderStatus, expected: tuple[OrderStatus, ...]) -> None:
    assert allowed_next_statuses(current) == expected
