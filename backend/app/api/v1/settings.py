"""ADHS settings endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import standard_rate_limit
from app.models.user import User
from app.schemas.settings import ADHSSettingsResponse, ADHSSettingsUpdate
from app.services.settings import SettingsService


router = APIRouter(tags=["Settings"])


@router.get(
    "/adhs",
    response_model=ADHSSettingsResponse,
    summary="Get ADHS settings",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_adhs_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get ADHS settings for the authenticated user (defaults if none exist)."""
    service = SettingsService(db)
    return await service.get_settings(current_user.id)


@router.put(
    "/adhs",
    response_model=ADHSSettingsResponse,
    summary="Update ADHS settings",
    dependencies=[Depends(standard_rate_limit)],
)
async def update_adhs_settings(
    data: ADHSSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update ADHS settings (partial update: only provided fields are changed)."""
    service = SettingsService(db)
    return await service.update_settings(current_user.id, data)
