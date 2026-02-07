"""Dashboard service for aggregating summary data."""

import random
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.nudge_history import NudgeHistory
from app.models.task import Task, TaskStatus
from app.schemas.dashboard import (
    DashboardDeadline,
    DashboardGamification,
    DashboardSummaryResponse,
    DashboardTask,
)
from app.services.gamification import GamificationService


MOTIVATIONAL_QUOTES = [
    "Jeder grosse Schritt beginnt mit einem kleinen. Du schaffst das!",
    "Du musst nicht perfekt sein. Du musst nur anfangen.",
    "Fortschritt ist Fortschritt, egal wie klein.",
    "Dein Gehirn ist anders verdrahtet -- und das ist eine Superkraft.",
    "Ein Task nach dem anderen. Du bist auf dem richtigen Weg!",
    "Vergiss nicht: Pausen sind auch produktiv.",
    "Heute ist ein guter Tag, um etwas zu erledigen.",
    "Kleine Schritte fuehren zu grossen Veraenderungen.",
    "Du hast schon so viel geschafft. Weiter so!",
    "Fokus ist ein Muskel. Jedes Mal wird es ein bisschen leichter.",
]


class DashboardService:
    """Service for dashboard aggregation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_summary(self, user_id: UUID) -> DashboardSummaryResponse:
        """Get aggregated dashboard summary."""
        # 1. Today's tasks (due today or open/in_progress with due date today)
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        tasks_result = await self.db.execute(
            select(Task)
            .where(
                Task.user_id == user_id,
                Task.status.in_([TaskStatus.OPEN, TaskStatus.IN_PROGRESS]),
            )
            .order_by(Task.priority.desc(), Task.due_date.asc().nullslast())
            .limit(10)
        )
        today_tasks_raw = list(tasks_result.scalars().all())

        today_tasks = [
            DashboardTask(
                id=t.id,
                title=t.title,
                priority=t.priority.value,
                status=t.status.value,
                due_date=t.due_date,
                estimated_minutes=t.estimated_minutes,
            )
            for t in today_tasks_raw
        ]

        # 2. Gamification stats
        gamification_service = GamificationService(self.db)
        stats = await gamification_service.get_stats(user_id)

        gamification = DashboardGamification(
            total_xp=stats.total_xp,
            level=stats.level,
            streak=stats.current_streak,
            progress_percent=stats.progress_percent,
        )

        # 3. Next deadline
        deadline_result = await self.db.execute(
            select(Task)
            .where(
                Task.user_id == user_id,
                Task.status.in_([TaskStatus.OPEN, TaskStatus.IN_PROGRESS]),
                Task.due_date.is_not(None),
                Task.due_date >= now,
            )
            .order_by(Task.due_date.asc())
            .limit(1)
        )
        next_task = deadline_result.scalar_one_or_none()
        next_deadline = None
        if next_task:
            next_deadline = DashboardDeadline(
                task_title=next_task.title,
                due_date=next_task.due_date,
            )

        # 4. Active nudges count
        nudge_count_result = await self.db.execute(
            select(func.count())
            .select_from(NudgeHistory)
            .where(
                NudgeHistory.user_id == user_id,
                NudgeHistory.acknowledged_at.is_(None),
            )
        )
        active_nudges_count = nudge_count_result.scalar_one()

        # 5. Motivational quote
        quote = random.choice(MOTIVATIONAL_QUOTES)

        return DashboardSummaryResponse(
            today_tasks=today_tasks,
            gamification=gamification,
            next_deadline=next_deadline,
            active_nudges_count=active_nudges_count,
            motivational_quote=quote,
        )
