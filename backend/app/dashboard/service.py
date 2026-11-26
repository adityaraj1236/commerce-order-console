import logging

from sqlalchemy.orm import Session

from app.core.logging import log_with_context
from app.dashboard import crud
from app.dashboard.schemas import DashboardSummary, OrderStats, ProductStats
from app.orders.models import OrderStatus

logger = logging.getLogger(__name__)


def get_summary(session: Session, low_stock_threshold: int) -> DashboardSummary:
    counts = crud.count_orders_by_status(session)
    # Every status is always present, so the UI never has to handle a missing key.
    by_status = {status: counts.get(status, 0) for status in OrderStatus}
    total_products, low_stock, out_of_stock = crud.count_products_by_stock_level(
        session, low_stock_threshold
    )

    summary = DashboardSummary(
        orders=OrderStats(total=sum(by_status.values()), by_status=by_status),
        products=ProductStats(
            total=total_products,
            low_stock=low_stock,
            out_of_stock=out_of_stock,
            low_stock_threshold=low_stock_threshold,
        ),
    )
    log_with_context(
        logger,
        "INFO",
        "DASHBOARD: Summary computed (service.py get_summary)",
        context={"total_orders": summary.orders.total, "low_stock": low_stock},
    )
    return summary
