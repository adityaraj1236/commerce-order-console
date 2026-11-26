from fastapi import APIRouter

from app.core.config import get_settings
from app.dashboard import service
from app.dashboard.schemas import DashboardSummary
from app.db.session import DbSession

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummary,
    summary="Order counts by status and product stock levels",
)
def get_summary(session: DbSession) -> DashboardSummary:
    return service.get_summary(session, get_settings().low_stock_threshold)
