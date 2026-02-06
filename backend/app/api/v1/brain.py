"""Brain (Second Brain) management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import standard_rate_limit
from app.models.user import User
from app.schemas.brain import (
    BrainEntryCreate,
    BrainEntryUpdate,
    BrainEntryResponse,
    BrainSearchResult,
)
from app.services.brain import BrainService


router = APIRouter(tags=["Brain"])


@router.post(
    "/entries",
    response_model=BrainEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create brain entry",
    dependencies=[Depends(standard_rate_limit)],
)
async def create_entry(
    data: BrainEntryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new brain entry."""
    service = BrainService(db)
    entry = await service.create_entry(current_user.id, data)
    return BrainEntryResponse.model_validate(entry)


@router.get(
    "/entries",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="List brain entries",
    dependencies=[Depends(standard_rate_limit)],
)
async def list_entries(
    cursor: UUID | None = Query(None, description="Cursor for pagination"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    entry_type: str | None = Query(None, description="Filter by entry type"),
    tags: list[str] | None = Query(None, description="Filter by tags"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get paginated list of brain entries."""
    service = BrainService(db)
    entries, next_cursor, has_more, total_count = await service.get_entries(
        user_id=current_user.id,
        cursor=cursor,
        limit=limit,
        entry_type=entry_type,
        tags=tags,
    )

    return {
        "items": [BrainEntryResponse.model_validate(e) for e in entries],
        "next_cursor": str(next_cursor) if next_cursor else None,
        "has_more": has_more,
        "total_count": total_count,
    }


@router.get(
    "/entries/{entry_id}",
    response_model=BrainEntryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get brain entry",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_entry(
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific brain entry by ID."""
    service = BrainService(db)
    entry = await service.get_entry(entry_id, current_user.id)
    return BrainEntryResponse.model_validate(entry)


@router.put(
    "/entries/{entry_id}",
    response_model=BrainEntryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update brain entry",
    dependencies=[Depends(standard_rate_limit)],
)
async def update_entry(
    entry_id: UUID,
    data: BrainEntryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing brain entry."""
    service = BrainService(db)
    entry = await service.update_entry(entry_id, current_user.id, data)
    return BrainEntryResponse.model_validate(entry)


@router.delete(
    "/entries/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete brain entry",
    dependencies=[Depends(standard_rate_limit)],
)
async def delete_entry(
    entry_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a brain entry."""
    service = BrainService(db)
    await service.delete_entry(entry_id, current_user.id)


@router.get(
    "/search",
    response_model=list[BrainSearchResult],
    status_code=status.HTTP_200_OK,
    summary="Search brain entries",
    dependencies=[Depends(standard_rate_limit)],
)
async def search_entries(
    q: str = Query(..., min_length=1, max_length=500, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    min_score: float = Query(0.5, ge=0.0, le=1.0, description="Minimum relevance score"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Search brain entries by text content."""
    service = BrainService(db)
    return await service.search(
        user_id=current_user.id,
        query=q,
        limit=limit,
        min_score=min_score,
    )
