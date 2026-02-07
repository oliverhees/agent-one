"""Gamification service for managing XP, levels, and streaks."""

import math
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus
from app.models.user_stats import UserStats
from app.schemas.gamification import GamificationStatsResponse, XPHistoryEntry


class GamificationService:
    """Service for gamification operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def calculate_level(total_xp: int) -> int:
        """Calculate level from total XP. Formula: floor(sqrt(total_xp / 100)), min 1."""
        if total_xp <= 0:
            return 1
        return max(1, int(math.floor(math.sqrt(total_xp / 100))))

    @staticmethod
    def xp_for_next_level(level: int) -> int:
        """Calculate XP threshold for the next level. Formula: ((level + 1) ** 2) * 100."""
        return ((level + 1) ** 2) * 100

    @staticmethod
    def calculate_progress(total_xp: int, level: int) -> float:
        """Calculate progress percentage to next level."""
        current_level_xp = (level ** 2) * 100
        next_level_xp = ((level + 1) ** 2) * 100
        xp_range = next_level_xp - current_level_xp
        if xp_range <= 0:
            return 0.0
        xp_in_level = total_xp - current_level_xp
        progress = (xp_in_level / xp_range) * 100.0
        return round(min(100.0, max(0.0, progress)), 1)

    async def get_or_create_stats(self, user_id: UUID) -> UserStats:
        """Get user stats, creating them if they don't exist."""
        result = await self.db.execute(
            select(UserStats).where(UserStats.user_id == user_id)
        )
        stats = result.scalar_one_or_none()

        if not stats:
            stats = UserStats(
                user_id=user_id,
                total_xp=0,
                level=1,
                current_streak=0,
                longest_streak=0,
                tasks_completed=0,
            )
            self.db.add(stats)
            await self.db.flush()
            await self.db.refresh(stats)

        return stats

    async def get_stats(self, user_id: UUID) -> GamificationStatsResponse:
        """Get gamification stats with computed fields."""
        stats = await self.get_or_create_stats(user_id)

        level = self.calculate_level(stats.total_xp)
        next_level_xp = self.xp_for_next_level(level)
        progress = self.calculate_progress(stats.total_xp, level)

        return GamificationStatsResponse(
            total_xp=stats.total_xp,
            level=level,
            current_streak=stats.current_streak,
            longest_streak=stats.longest_streak,
            xp_for_next_level=next_level_xp,
            progress_percent=progress,
            tasks_completed=stats.tasks_completed,
        )

    async def get_history(self, user_id: UUID, days: int = 30) -> list[XPHistoryEntry]:
        """Get XP history per day from completed tasks."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self.db.execute(
            select(
                cast(Task.completed_at, Date).label("day"),
                func.coalesce(func.sum(Task.xp_earned), 0).label("xp_earned"),
                func.count(Task.id).label("tasks_completed"),
            )
            .where(
                Task.user_id == user_id,
                Task.status == TaskStatus.DONE,
                Task.completed_at.is_not(None),
                Task.completed_at >= cutoff,
            )
            .group_by(cast(Task.completed_at, Date))
            .order_by(cast(Task.completed_at, Date).desc())
        )
        rows = result.all()

        return [
            XPHistoryEntry(
                date=str(row.day),
                xp_earned=int(row.xp_earned),
                tasks_completed=int(row.tasks_completed),
            )
            for row in rows
        ]

    async def update_stats_on_complete(self, user_id: UUID, xp_earned: int) -> UserStats:
        """Update user stats after a task completion."""
        stats = await self.get_or_create_stats(user_id)

        stats.total_xp += xp_earned
        stats.tasks_completed += 1
        stats.level = self.calculate_level(stats.total_xp)

        await self.db.flush()
        await self.db.refresh(stats)

        return stats

    async def update_streak(self, user_id: UUID) -> UserStats:
        """Update streak based on last_active_date."""
        stats = await self.get_or_create_stats(user_id)

        today = date.today()

        if stats.last_active_date is None:
            stats.current_streak = 1
        elif stats.last_active_date == today:
            # Already active today, no change
            pass
        elif stats.last_active_date == today - timedelta(days=1):
            # Consecutive day
            stats.current_streak += 1
        else:
            # Streak broken
            stats.current_streak = 1

        stats.last_active_date = today

        if stats.current_streak > stats.longest_streak:
            stats.longest_streak = stats.current_streak

        await self.db.flush()
        await self.db.refresh(stats)

        return stats
