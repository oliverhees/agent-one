"""Calendar API endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.calendar import CalendarEventListResponse, CalendarEventResponse, CalendarStatusResponse
from app.services.calendar import CalendarService

router = APIRouter(tags=["Calendar"])


@router.get("/status", response_model=CalendarStatusResponse)
async def get_calendar_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CalendarService(db)
    status = await service.get_connection_status(str(current_user.id))
    return CalendarStatusResponse(**status)


@router.get("/events", response_model=CalendarEventListResponse)
async def get_today_events(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CalendarService(db)
    events = await service.get_today_events(str(current_user.id))
    return CalendarEventListResponse(events=events, total=len(events))


@router.get("/events/upcoming", response_model=CalendarEventListResponse)
async def get_upcoming_events(
    hours: int = 24,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CalendarService(db)
    events = await service.get_upcoming_events(str(current_user.id), hours=hours)
    return CalendarEventListResponse(events=events, total=len(events))


@router.post("/sync")
async def sync_calendar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CalendarService(db)
    events = await service.sync_events(str(current_user.id))
    await db.commit()
    return {"synced_count": len(events)}


@router.delete("/disconnect")
async def disconnect_calendar(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = CalendarService(db)
    await service.disconnect(str(current_user.id))
    await db.commit()
    return {"message": "Calendar disconnected"}


@router.get("/auth/google")
async def google_auth_start(
    current_user: User = Depends(get_current_user),
):
    from app.core.config import settings
    url = CalendarService.build_google_auth_url(settings.google_redirect_uri, str(current_user.id))
    return {"auth_url": url}


@router.get("/auth/google/callback")
async def google_auth_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    from app.core.config import settings
    service = CalendarService(db)
    success = await service.exchange_code(state, code, settings.google_redirect_uri)
    if not success:
        raise HTTPException(status_code=400, detail="OAuth token exchange failed")
    await db.commit()
    return {"message": "Calendar connected successfully"}
