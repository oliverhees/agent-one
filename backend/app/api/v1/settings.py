"""ADHS settings endpoints."""

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import standard_rate_limit
from app.models.user import User
from app.schemas.settings import (
    ADHSSettingsResponse,
    ADHSSettingsUpdate,
    ApiKeyResponse,
    ApiKeyUpdate,
    OnboardingRequest,
    OnboardingResponse,
    VoiceProviderResponse,
    VoiceProviderUpdate,
)
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


@router.post(
    "/onboarding",
    response_model=OnboardingResponse,
    summary="Complete onboarding",
    dependencies=[Depends(standard_rate_limit)],
)
async def complete_onboarding(
    data: OnboardingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Complete user onboarding by saving initial preferences and marking onboarding as done.

    All fields are optional. If display_name is not provided, user can skip name input.
    """
    service = SettingsService(db)

    # Build update dict from provided fields
    update_data = data.model_dump(exclude_unset=True)

    await service.complete_onboarding(current_user.id, update_data)

    return OnboardingResponse(
        success=True,
        message="Onboarding abgeschlossen"
    )


@router.get(
    "/api-keys",
    response_model=ApiKeyResponse,
    summary="Get API keys (masked)",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get API keys for the authenticated user (masked, e.g. '...XXXX').

    Only the last 4 characters are shown for security.
    """
    service = SettingsService(db)
    return await service.get_api_keys(current_user.id)


@router.put(
    "/api-keys",
    response_model=ApiKeyResponse,
    summary="Save API keys (encrypted)",
    dependencies=[Depends(standard_rate_limit)],
)
async def save_api_keys(
    data: ApiKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Save API keys (encrypted) for the authenticated user.

    Only provided keys are updated. Existing keys are preserved if not included.
    Returns masked keys (e.g. '...XXXX') for security.
    """
    service = SettingsService(db)
    return await service.save_api_keys(current_user.id, data)


@router.get(
    "/voice-providers",
    response_model=VoiceProviderResponse,
    summary="Get voice provider settings",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_voice_providers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get voice provider settings (STT and TTS) for the authenticated user."""
    service = SettingsService(db)
    return await service.get_voice_providers(current_user.id)


@router.put(
    "/voice-providers",
    response_model=VoiceProviderResponse,
    summary="Update voice provider settings",
    dependencies=[Depends(standard_rate_limit)],
)
async def update_voice_providers(
    data: VoiceProviderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update voice provider settings (STT and TTS).

    Valid STT providers: 'deepgram', 'whisper'
    Valid TTS providers: 'elevenlabs', 'edge-tts'
    """
    service = SettingsService(db)
    return await service.update_voice_providers(current_user.id, data)
