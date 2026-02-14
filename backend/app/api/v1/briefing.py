"""Morning Briefing API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import standard_rate_limit
from app.models.user import User
from app.models.user_settings import DEFAULT_SETTINGS
from app.schemas.briefing import (
    BriefingResponse,
    BriefingHistoryResponse,
    BrainDumpRequest,
    BrainDumpResponse,
)
from app.services.briefing import BriefingService
from app.services.brain_dump import BrainDumpService

router = APIRouter(tags=["Briefing"])


@router.get(
    "/today",
    response_model=BriefingResponse | None,
    summary="Get today's Morning Briefing",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_today_briefing(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get today's briefing if it exists. Returns null if not yet generated."""
    service = BriefingService(db)
    return await service.get_today_briefing(str(current_user.id))


@router.post(
    "/generate",
    response_model=BriefingResponse,
    summary="Generate today's Morning Briefing",
    dependencies=[Depends(standard_rate_limit)],
)
async def generate_briefing(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a new Morning Briefing for today (or return existing one)."""
    service = BriefingService(db)

    # Check if already exists
    existing = await service.get_today_briefing(str(current_user.id))
    if existing:
        return BriefingResponse(**existing)

    # Get user settings for display_name and max_daily_tasks
    settings = {}
    if current_user.user_settings:
        settings = {**DEFAULT_SETTINGS, **current_user.user_settings.settings}
    display_name = settings.get("display_name")
    max_tasks = settings.get("max_daily_tasks", 3)

    result = await service.generate_briefing(
        str(current_user.id),
        display_name=display_name,
        max_tasks=max_tasks,
    )
    await db.commit()
    return BriefingResponse(**result)


@router.get(
    "/history",
    response_model=BriefingHistoryResponse,
    summary="Get briefing history",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_briefing_history(
    days: int = Query(default=7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get briefing history for the last N days."""
    service = BriefingService(db)
    briefings = await service.get_briefing_history(str(current_user.id), days=days)
    return BriefingHistoryResponse(
        briefings=[BriefingResponse(**b) for b in briefings],
        days=days,
    )


@router.put(
    "/{briefing_id}/read",
    summary="Mark briefing as read",
    dependencies=[Depends(standard_rate_limit)],
)
async def mark_briefing_read(
    briefing_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Mark a briefing as read."""
    service = BriefingService(db)
    success = await service.mark_as_read(briefing_id, str(current_user.id))
    if not success:
        raise HTTPException(status_code=404, detail="Briefing not found")
    await db.commit()
    return {"status": "read"}


@router.post(
    "/brain-dump",
    response_model=BrainDumpResponse,
    summary="Process brain dump into tasks",
    dependencies=[Depends(standard_rate_limit)],
)
async def brain_dump(
    data: BrainDumpRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Parse free-text brain dump and create tasks automatically."""
    service = BrainDumpService(db)
    result = await service.process(str(current_user.id), data.text)
    await db.commit()
    return BrainDumpResponse(**result)
