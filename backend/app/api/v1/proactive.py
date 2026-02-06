"""Proactive extraction endpoints for mentioned items."""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import standard_rate_limit
from app.models.user import User
from app.schemas.proactive import MentionedItemResponse, MentionedItemConvertRequest
from app.services.proactive import ProactiveService


router = APIRouter(tags=["Proactive"])


class SnoozeRequest(BaseModel):
    """Schema for snoozing a mentioned item."""

    until: datetime = Field(..., description="Snooze until this timestamp")


@router.get(
    "/mentioned-items",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List mentioned items",
    dependencies=[Depends(standard_rate_limit)],
)
async def list_mentioned_items(
    cursor: UUID | None = Query(None, description="Cursor for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    item_status: str | None = Query(None, alias="status", description="Filter by status"),
    item_type: str | None = Query(None, description="Filter by item type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of mentioned items extracted from chat."""
    service = ProactiveService(db)
    items, next_cursor, has_more, total_count = await service.get_mentioned_items(
        user_id=current_user.id,
        cursor=cursor,
        limit=limit,
        status=item_status,
        item_type=item_type,
    )

    return {
        "items": [MentionedItemResponse.model_validate(i) for i in items],
        "next_cursor": str(next_cursor) if next_cursor else None,
        "has_more": has_more,
        "total_count": total_count,
    }


@router.post(
    "/mentioned-items/{item_id}/convert",
    response_model=MentionedItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Convert mentioned item",
    dependencies=[Depends(standard_rate_limit)],
)
async def convert_mentioned_item(
    item_id: UUID,
    data: MentionedItemConvertRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Convert a mentioned item to a task or brain entry."""
    service = ProactiveService(db)
    item = await service.convert_item(item_id, current_user.id, data.convert_to)
    return MentionedItemResponse.model_validate(item)


@router.post(
    "/mentioned-items/{item_id}/dismiss",
    response_model=MentionedItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Dismiss mentioned item",
    dependencies=[Depends(standard_rate_limit)],
)
async def dismiss_mentioned_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Dismiss a mentioned item."""
    service = ProactiveService(db)
    item = await service.dismiss_item(item_id, current_user.id)
    return MentionedItemResponse.model_validate(item)


@router.post(
    "/mentioned-items/{item_id}/snooze",
    response_model=MentionedItemResponse,
    status_code=status.HTTP_200_OK,
    summary="Snooze mentioned item",
    dependencies=[Depends(standard_rate_limit)],
)
async def snooze_mentioned_item(
    item_id: UUID,
    data: SnoozeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Snooze a mentioned item until a specified time."""
    service = ProactiveService(db)
    item = await service.snooze_item(item_id, current_user.id, data.until)
    return MentionedItemResponse.model_validate(item)
