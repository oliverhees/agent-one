"""Reminder API endpoints."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.reminder import Reminder, ReminderStatus
from app.models.user import User
from app.schemas.reminder import (
    ReminderCreate, ReminderListResponse, ReminderResponse,
    ReminderSnoozeRequest, ReminderUpdate,
)

router = APIRouter(tags=["Reminders"])


@router.get("", response_model=ReminderListResponse)
async def list_reminders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    count_stmt = select(func.count()).select_from(Reminder).where(Reminder.user_id == current_user.id)
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = select(Reminder).where(Reminder.user_id == current_user.id).order_by(Reminder.remind_at)
    result = await db.execute(stmt)
    reminders = result.scalars().all()

    def to_response(r: Reminder) -> ReminderResponse:
        return ReminderResponse(
            id=str(r.id),
            user_id=str(r.user_id),
            title=r.title,
            description=r.description,
            remind_at=r.remind_at,
            source=r.source,
            status=r.status,
            recurrence=r.recurrence,
            recurrence_end=r.recurrence_end,
            linked_task_id=str(r.linked_task_id) if r.linked_task_id else None,
            linked_event_id=str(r.linked_event_id) if r.linked_event_id else None,
            created_at=r.created_at,
        )

    return ReminderListResponse(
        reminders=[to_response(r) for r in reminders],
        total=total,
    )


@router.get("/upcoming", response_model=ReminderListResponse)
async def list_upcoming_reminders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Reminder)
        .where(Reminder.user_id == current_user.id, Reminder.status == ReminderStatus.PENDING)
        .order_by(Reminder.remind_at)
    )
    result = await db.execute(stmt)
    reminders = result.scalars().all()

    def to_response(r: Reminder) -> ReminderResponse:
        return ReminderResponse(
            id=str(r.id),
            user_id=str(r.user_id),
            title=r.title,
            description=r.description,
            remind_at=r.remind_at,
            source=r.source,
            status=r.status,
            recurrence=r.recurrence,
            recurrence_end=r.recurrence_end,
            linked_task_id=str(r.linked_task_id) if r.linked_task_id else None,
            linked_event_id=str(r.linked_event_id) if r.linked_event_id else None,
            created_at=r.created_at,
        )

    return ReminderListResponse(
        reminders=[to_response(r) for r in reminders],
        total=len(reminders),
    )


@router.post("", response_model=ReminderResponse, status_code=201)
async def create_reminder(
    body: ReminderCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    reminder = Reminder(
        user_id=current_user.id,
        title=body.title,
        description=body.description,
        remind_at=body.remind_at,
        source=body.source,
        recurrence=body.recurrence,
        recurrence_end=body.recurrence_end,
        linked_task_id=UUID(body.linked_task_id) if body.linked_task_id else None,
        linked_event_id=UUID(body.linked_event_id) if body.linked_event_id else None,
    )
    db.add(reminder)
    await db.commit()
    await db.refresh(reminder)

    # Convert UUID fields to strings for response
    return ReminderResponse(
        id=str(reminder.id),
        user_id=str(reminder.user_id),
        title=reminder.title,
        description=reminder.description,
        remind_at=reminder.remind_at,
        source=reminder.source,
        status=reminder.status,
        recurrence=reminder.recurrence,
        recurrence_end=reminder.recurrence_end,
        linked_task_id=str(reminder.linked_task_id) if reminder.linked_task_id else None,
        linked_event_id=str(reminder.linked_event_id) if reminder.linked_event_id else None,
        created_at=reminder.created_at,
    )


@router.put("/{reminder_id}", response_model=ReminderResponse)
async def update_reminder(
    reminder_id: UUID,
    body: ReminderUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
    result = await db.execute(stmt)
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(reminder, key, value)

    await db.commit()
    await db.refresh(reminder)

    return ReminderResponse(
        id=str(reminder.id),
        user_id=str(reminder.user_id),
        title=reminder.title,
        description=reminder.description,
        remind_at=reminder.remind_at,
        source=reminder.source,
        status=reminder.status,
        recurrence=reminder.recurrence,
        recurrence_end=reminder.recurrence_end,
        linked_task_id=str(reminder.linked_task_id) if reminder.linked_task_id else None,
        linked_event_id=str(reminder.linked_event_id) if reminder.linked_event_id else None,
        created_at=reminder.created_at,
    )


@router.delete("/{reminder_id}")
async def delete_reminder(
    reminder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
    result = await db.execute(stmt)
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    await db.delete(reminder)
    await db.commit()
    return {"message": "Reminder deleted"}


@router.post("/{reminder_id}/snooze", response_model=ReminderResponse)
async def snooze_reminder(
    reminder_id: UUID,
    body: ReminderSnoozeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
    result = await db.execute(stmt)
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    reminder.remind_at = body.snooze_until
    reminder.status = ReminderStatus.SNOOZED
    await db.commit()
    await db.refresh(reminder)

    return ReminderResponse(
        id=str(reminder.id),
        user_id=str(reminder.user_id),
        title=reminder.title,
        description=reminder.description,
        remind_at=reminder.remind_at,
        source=reminder.source,
        status=reminder.status,
        recurrence=reminder.recurrence,
        recurrence_end=reminder.recurrence_end,
        linked_task_id=str(reminder.linked_task_id) if reminder.linked_task_id else None,
        linked_event_id=str(reminder.linked_event_id) if reminder.linked_event_id else None,
        created_at=reminder.created_at,
    )


@router.post("/{reminder_id}/dismiss", response_model=ReminderResponse)
async def dismiss_reminder(
    reminder_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Reminder).where(Reminder.id == reminder_id, Reminder.user_id == current_user.id)
    result = await db.execute(stmt)
    reminder = result.scalar_one_or_none()
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    reminder.status = ReminderStatus.DISMISSED
    await db.commit()
    await db.refresh(reminder)

    return ReminderResponse(
        id=str(reminder.id),
        user_id=str(reminder.user_id),
        title=reminder.title,
        description=reminder.description,
        remind_at=reminder.remind_at,
        source=reminder.source,
        status=reminder.status,
        recurrence=reminder.recurrence,
        recurrence_end=reminder.recurrence_end,
        linked_task_id=str(reminder.linked_task_id) if reminder.linked_task_id else None,
        linked_event_id=str(reminder.linked_event_id) if reminder.linked_event_id else None,
        created_at=reminder.created_at,
    )
