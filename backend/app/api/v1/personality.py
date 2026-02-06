"""Personality profile management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import standard_rate_limit
from app.models.user import User
from app.schemas.personality import (
    PersonalityProfileCreate,
    PersonalityProfileUpdate,
    PersonalityProfileResponse,
    PersonalityTemplateResponse,
)
from app.services.personality import PersonalityService


router = APIRouter(tags=["Personality"])


@router.post(
    "/profiles",
    response_model=PersonalityProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create personality profile",
    dependencies=[Depends(standard_rate_limit)],
)
async def create_profile(
    data: PersonalityProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new personality profile, optionally based on a template."""
    service = PersonalityService(db)
    profile = await service.create_profile(current_user.id, data)
    return PersonalityProfileResponse.model_validate(profile)


@router.get(
    "/profiles",
    response_model=list[PersonalityProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="List personality profiles",
    dependencies=[Depends(standard_rate_limit)],
)
async def list_profiles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all personality profiles for the authenticated user."""
    service = PersonalityService(db)
    profiles = await service.get_profiles(current_user.id)
    return [PersonalityProfileResponse.model_validate(p) for p in profiles]


@router.get(
    "/profiles/{profile_id}",
    response_model=PersonalityProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Get personality profile",
    dependencies=[Depends(standard_rate_limit)],
)
async def get_profile(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific personality profile by ID."""
    service = PersonalityService(db)
    profile = await service.get_profile(profile_id, current_user.id)
    return PersonalityProfileResponse.model_validate(profile)


@router.put(
    "/profiles/{profile_id}",
    response_model=PersonalityProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Update personality profile",
    dependencies=[Depends(standard_rate_limit)],
)
async def update_profile(
    profile_id: UUID,
    data: PersonalityProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing personality profile."""
    service = PersonalityService(db)
    profile = await service.update_profile(profile_id, current_user.id, data)
    return PersonalityProfileResponse.model_validate(profile)


@router.delete(
    "/profiles/{profile_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete personality profile",
    dependencies=[Depends(standard_rate_limit)],
)
async def delete_profile(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a personality profile. Active profiles cannot be deleted."""
    service = PersonalityService(db)
    await service.delete_profile(profile_id, current_user.id)


@router.post(
    "/profiles/{profile_id}/activate",
    response_model=PersonalityProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate personality profile",
    dependencies=[Depends(standard_rate_limit)],
)
async def activate_profile(
    profile_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Activate a personality profile. Deactivates the currently active one."""
    service = PersonalityService(db)
    profile = await service.activate_profile(profile_id, current_user.id)
    return PersonalityProfileResponse.model_validate(profile)


@router.get(
    "/templates",
    response_model=list[PersonalityTemplateResponse],
    status_code=status.HTTP_200_OK,
    summary="List personality templates",
    dependencies=[Depends(standard_rate_limit)],
)
async def list_templates(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all available personality templates."""
    service = PersonalityService(db)
    templates = await service.get_templates()
    return [PersonalityTemplateResponse.model_validate(t) for t in templates]
