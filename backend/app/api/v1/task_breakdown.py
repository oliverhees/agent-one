"""Task breakdown endpoints for AI-powered task decomposition."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import RateLimiter, standard_rate_limit
from app.models.user import User
from app.schemas.task_breakdown import (
    BreakdownConfirmRequest,
    BreakdownConfirmResponse,
    BreakdownResponse,
)
from app.services.task_breakdown import TaskBreakdownService


router = APIRouter(tags=["Task Breakdown"])

# AI endpoint has stricter rate limit
ai_rate_limit = RateLimiter(times=10, seconds=60)


@router.post(
    "/{task_id}/breakdown",
    response_model=BreakdownResponse,
    summary="Generate task breakdown",
    dependencies=[Depends(ai_rate_limit)],
)
async def generate_breakdown(
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate AI-powered sub-task suggestions for a task (3-7 steps)."""
    service = TaskBreakdownService(db)
    return await service.generate_breakdown(task_id, current_user.id)


@router.post(
    "/{task_id}/breakdown/confirm",
    response_model=BreakdownConfirmResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Confirm task breakdown",
    dependencies=[Depends(standard_rate_limit)],
)
async def confirm_breakdown(
    task_id: UUID,
    data: BreakdownConfirmRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Confirm and create sub-tasks from a breakdown suggestion."""
    service = TaskBreakdownService(db)
    return await service.confirm_breakdown(task_id, current_user.id, data.subtasks)
