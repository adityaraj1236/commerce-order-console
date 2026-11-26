"""Order fulfilment state machine: the single source of truth for allowed status changes.

    PLACED ──► PACKED ──► SHIPPED
       │          │
       └──────────┴──► CANCELLED

SHIPPED and CANCELLED are terminal. Pure logic, no database access, so it is unit tested directly.
"""

from app.orders.models import OrderStatus

ALLOWED_TRANSITIONS: dict[OrderStatus, tuple[OrderStatus, ...]] = {
    OrderStatus.PLACED: (OrderStatus.PACKED, OrderStatus.CANCELLED),
    OrderStatus.PACKED: (OrderStatus.SHIPPED, OrderStatus.CANCELLED),
    OrderStatus.SHIPPED: (),
    OrderStatus.CANCELLED: (),
}


def allowed_next_statuses(current: OrderStatus) -> tuple[OrderStatus, ...]:
    return ALLOWED_TRANSITIONS[current]


def can_transition(current: OrderStatus, target: OrderStatus) -> bool:
    return target in ALLOWED_TRANSITIONS[current]
