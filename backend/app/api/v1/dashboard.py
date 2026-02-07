"""Dashboard endpoint for aggregated summary data."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import standard_rate_limit
from app.models.user import User
from app.schemas.dashboard import DashboardSummaryResponse
from app.services.dashboard import DashboardService


router = APIRouter(tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Get dashboard summary",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get aggregated dashboard data: tasks, gamification, deadline, nudges, quote."""
    service = DashboardService(db)
    return await service.get_summary(current_user.id)
