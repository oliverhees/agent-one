"""Nudge endpoints for ADHS reminders."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import standard_rate_limit
from app.models.user import User
from app.schemas.nudge import (
    NudgeAcknowledgeResponse,
    NudgeHistoryResponse,
    NudgeListResponse,
)
from app.services.nudge import NudgeService


router = APIRouter(tags=["Nudges"])


@router.get(
    "",
    response_model=NudgeListResponse,
    summary="Get active nudges",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_active_nudges(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all active (unacknowledged) nudges for the authenticated user."""
    service = NudgeService(db)
    return await service.get_active_nudges(current_user.id)


@router.post(
    "/{nudge_id}/acknowledge",
    response_model=NudgeAcknowledgeResponse,
    summary="Acknowledge nudge",
    dependencies=[Depends(standard_rate_limit)],
)
async def acknowledge_nudge(
    nudge_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Acknowledge a nudge (mark as read)."""
    service = NudgeService(db)
    return await service.acknowledge_nudge(nudge_id, current_user.id)


@router.get(
    "/history",
    response_model=NudgeHistoryResponse,
    summary="Get nudge history",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_nudge_history(
    cursor: UUID | None = Query(None, description="Cursor for pagination"),
    limit: int = Query(50, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated nudge history (including acknowledged nudges)."""
    service = NudgeService(db)
    return await service.get_history(current_user.id, cursor=cursor, limit=limit)
