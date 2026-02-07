"""ADHS settings endpoints."""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import standard_rate_limit
from app.models.user import User
from app.schemas.settings import ADHSSettingsResponse, ADHSSettingsUpdate
from app.services.settings import SettingsService


class PushTokenRequest(BaseModel):
    """Request body for registering an Expo push token."""

    expo_push_token: str = Field(..., min_length=10, description="Expo push token (ExponentPushToken[...])")


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


@router.post(
    "/push-token",
    status_code=204,
    summary="Register Expo push token",
    dependencies=[Depends(standard_rate_limit)],
)
async def register_push_token(
    data: PushTokenRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register or update the Expo push notification token for the authenticated user."""
    service = SettingsService(db)
    await service.register_push_token(current_user.id, data.expo_push_token)
    return Response(status_code=204)
