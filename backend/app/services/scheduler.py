"""Background scheduler for automated nudges and push notifications."""

import asyncio
import logging
from datetime import datetime, date, timedelta, time
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.nudge_history import NudgeHistory, NudgeType
from app.models.task import Task, TaskStatus
from app.models.user_settings import UserSettings, DEFAULT_SETTINGS
from app.models.user_stats import UserStats
from app.services.notification import NotificationService, PushNotification
from app.services.nudge import NudgeService

logger = logging.getLogger(__name__)

SCHEDULER_INTERVAL_SECONDS = 300  # 5 minutes
BERLIN_TZ = ZoneInfo("Europe/Berlin")


async def run_scheduler() -> None:
    """Main scheduler loop — runs every 5 minutes."""
    logger.info("Background scheduler started (interval: %ds)", SCHEDULER_INTERVAL_SECONDS)

    while True:
        try:
            await _scheduler_tick()
        except asyncio.CancelledError:
            logger.info("Background scheduler cancelled — shutting down")
            raise
        except Exception:
            logger.exception("Scheduler tick failed")

        await asyncio.sleep(SCHEDULER_INTERVAL_SECONDS)


async def _scheduler_tick() -> None:
    """Single scheduler tick — checks all users with push tokens."""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(UserSettings))
        all_settings = result.scalars().all()

    eligible = []
    for us in all_settings:
        merged = {**DEFAULT_SETTINGS, **us.settings}
        token = merged.get("expo_push_token")
        enabled = merged.get("notifications_enabled", True)
        if token and enabled:
            eligible.append((us.user_id, token, merged))

    if not eligible:
        return

    logger.debug("Scheduler tick: %d eligible users", len(eligible))

    for user_id, token, settings in eligible:
        try:
            await _process_user(user_id, token, settings)
        except Exception:
            logger.exception("Scheduler error for user %s", user_id)


async def _process_user(user_id: UUID, token: str, settings: dict) -> None:
    """Process deadline/overdue/streak checks for one user."""
    now_berlin = datetime.now(BERLIN_TZ)

    # Respect quiet hours
    quiet_start = settings.get("quiet_hours_start")
    quiet_end = settings.get("quiet_hours_end")
    if quiet_start and quiet_end and _is_quiet_hours(now_berlin, quiet_start, quiet_end):
        return

    async with AsyncSessionLocal() as db:
        # 1. Deadline approaching (within 60 minutes)
        now_utc = datetime.now(BERLIN_TZ).astimezone(ZoneInfo("UTC"))
        deadline_cutoff = now_utc + timedelta(minutes=60)

        result = await db.execute(
            select(Task).where(
                Task.user_id == user_id,
                Task.status.in_([TaskStatus.OPEN, TaskStatus.IN_PROGRESS]),
                Task.due_date.isnot(None),
                Task.due_date > now_utc,
                Task.due_date <= deadline_cutoff,
            )
        )
        approaching_tasks = result.scalars().all()

        for task in approaching_tasks:
            if await _already_notified_today(db, user_id, task.id, NudgeType.DEADLINE):
                continue

            minutes_left = max(0, int((task.due_date - now_utc).total_seconds() / 60))
            level = 3 if minutes_left <= 30 else 2
            message = f"⏰ '{task.title}' ist in {minutes_left} Minuten faellig!"

            nudge_service = NudgeService(db)
            await nudge_service.create_nudge(user_id, task.id, level, NudgeType.DEADLINE, message)
            await db.commit()

            await NotificationService.send_notification(
                PushNotification(
                    to=token,
                    title="Deadline naht!",
                    body=message,
                    data={"type": "deadline", "task_id": str(task.id)},
                )
            )

        # 2. Overdue tasks
        result = await db.execute(
            select(Task).where(
                Task.user_id == user_id,
                Task.status.in_([TaskStatus.OPEN, TaskStatus.IN_PROGRESS]),
                Task.due_date.isnot(None),
                Task.due_date < now_utc,
            )
        )
        overdue_tasks = result.scalars().all()

        for task in overdue_tasks:
            if await _already_notified_today(db, user_id, task.id, NudgeType.MOTIVATIONAL):
                continue

            message = f"📋 '{task.title}' ist ueberfaellig — magst du sie erledigen oder verschieben?"

            nudge_service = NudgeService(db)
            await nudge_service.create_nudge(user_id, task.id, 2, NudgeType.MOTIVATIONAL, message)
            await db.commit()

            await NotificationService.send_notification(
                PushNotification(
                    to=token,
                    title="Aufgabe ueberfaellig",
                    body=message,
                    data={"type": "overdue", "task_id": str(task.id)},
                )
            )

        # 3. Streak reminder
        preferred_times = settings.get("preferred_reminder_times", [])
        if preferred_times and _is_near_reminder_time(now_berlin, preferred_times):
            stats_result = await db.execute(
                select(UserStats).where(UserStats.user_id == user_id)
            )
            stats = stats_result.scalar_one_or_none()

            if stats and stats.current_streak > 0:
                today = date.today()
                if stats.last_active_date != today:
                    if not await _already_notified_today(db, user_id, None, NudgeType.STREAK_REMINDER):
                        message = (
                            f"🔥 Dein Streak: {stats.current_streak} Tage! "
                            f"Erledige eine Aufgabe um ihn zu halten."
                        )

                        nudge_service = NudgeService(db)
                        await nudge_service.create_nudge(
                            user_id, None, 1, NudgeType.STREAK_REMINDER, message
                        )
                        await db.commit()

                        await NotificationService.send_notification(
                            PushNotification(
                                to=token,
                                title="Streak halten!",
                                body=message,
                                data={"type": "streak"},
                            )
                        )


def _is_quiet_hours(now: datetime, start_str: str, end_str: str) -> bool:
    """Check if current time falls within quiet hours (supports midnight spanning)."""
    start = time(int(start_str[:2]), int(start_str[3:5]))
    end = time(int(end_str[:2]), int(end_str[3:5]))
    current = now.time()

    if start <= end:
        # Same day range (e.g. 08:00–17:00)
        return start <= current <= end
    else:
        # Midnight spanning (e.g. 22:00–07:00)
        return current >= start or current <= end


def _is_near_reminder_time(now: datetime, reminder_times: list[str], window_minutes: int = 5) -> bool:
    """Check if current time is within a window of any preferred reminder time."""
    current_minutes = now.hour * 60 + now.minute
    for t_str in reminder_times:
        parts = t_str.split(":")
        if len(parts) == 2:
            target_minutes = int(parts[0]) * 60 + int(parts[1])
            if abs(current_minutes - target_minutes) <= window_minutes:
                return True
    return False


async def _already_notified_today(
    db: AsyncSession,
    user_id: UUID,
    task_id: UUID | None,
    nudge_type: NudgeType,
) -> bool:
    """Check if a nudge of this type was already sent today for this user/task."""
    today_start = datetime.combine(date.today(), time.min, tzinfo=BERLIN_TZ)

    filters = [
        NudgeHistory.user_id == user_id,
        NudgeHistory.nudge_type == nudge_type,
        NudgeHistory.delivered_at >= today_start,
    ]

    if task_id is not None:
        filters.append(NudgeHistory.task_id == task_id)
    else:
        filters.append(NudgeHistory.task_id.is_(None))

    result = await db.execute(
        select(func.count()).select_from(NudgeHistory).where(*filters)
    )
    count = result.scalar_one()
    return count > 0
