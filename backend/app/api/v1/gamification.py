"""Gamification endpoints for XP, levels, streaks, and achievements."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import standard_rate_limit
from app.models.user import User
from app.schemas.gamification import (
    AchievementListResponse,
    GamificationStatsResponse,
    XPHistoryResponse,
)
from app.services.achievement import AchievementService
from app.services.gamification import GamificationService


router = APIRouter(tags=["Gamification"])


@router.get(
    "/stats",
    response_model=GamificationStatsResponse,
    summary="Get gamification stats",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current XP, level, streak, and progress for the authenticated user."""
    service = GamificationService(db)
    return await service.get_stats(current_user.id)


@router.get(
    "/history",
    response_model=XPHistoryResponse,
    summary="Get XP history",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_history(
    days: int = Query(30, ge=1, le=365, description="Number of days back (max 365)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get XP history per day for charts and progress visualizations."""
    service = GamificationService(db)
    history = await service.get_history(current_user.id, days=days)
    return XPHistoryResponse(history=history, total_days=days)


@router.get(
    "/achievements",
    response_model=AchievementListResponse,
    summary="Get achievements",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all achievements with unlock status for the authenticated user."""
    service = AchievementService(db)
    return await service.get_achievements(current_user.id)
