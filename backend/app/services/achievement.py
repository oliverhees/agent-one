"""Achievement service for managing user achievements."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.achievement import Achievement, UserAchievement
from app.models.brain_entry import BrainEntry
from app.models.user_stats import UserStats
from app.schemas.gamification import AchievementResponse, AchievementListResponse


class AchievementService:
    """Service for achievement operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_achievements(self, user_id: UUID) -> AchievementListResponse:
        """Get all achievements with unlock status for a user."""
        # Get all active achievements
        result = await self.db.execute(
            select(Achievement).where(Achievement.is_active == True).order_by(Achievement.category, Achievement.name)
        )
        achievements = list(result.scalars().all())

        # Get user's unlocked achievements
        unlocked_result = await self.db.execute(
            select(UserAchievement).where(UserAchievement.user_id == user_id)
        )
        unlocked_map = {
            ua.achievement_id: ua.unlocked_at
            for ua in unlocked_result.scalars().all()
        }

        items = []
        unlocked_count = 0
        for ach in achievements:
            is_unlocked = ach.id in unlocked_map
            if is_unlocked:
                unlocked_count += 1
            items.append(AchievementResponse(
                id=ach.id,
                name=ach.name,
                description=ach.description,
                icon=ach.icon,
                category=ach.category.value,
                xp_reward=ach.xp_reward,
                unlocked=is_unlocked,
                unlocked_at=unlocked_map.get(ach.id),
            ))

        return AchievementListResponse(
            achievements=items,
            total_count=len(items),
            unlocked_count=unlocked_count,
        )

    async def check_and_unlock(self, user_id: UUID) -> list[Achievement]:
        """Check all achievement conditions and unlock any newly earned ones."""
        # Get user stats
        stats_result = await self.db.execute(
            select(UserStats).where(UserStats.user_id == user_id)
        )
        user_stats = stats_result.scalar_one_or_none()
        if not user_stats:
            return []

        # Count brain entries
        brain_count_result = await self.db.execute(
            select(func.count()).select_from(BrainEntry).where(BrainEntry.user_id == user_id)
        )
        brain_count = brain_count_result.scalar_one()

        # Get already unlocked achievement IDs
        unlocked_result = await self.db.execute(
            select(UserAchievement.achievement_id).where(UserAchievement.user_id == user_id)
        )
        unlocked_ids = {row[0] for row in unlocked_result.all()}

        # Get all active achievements not yet unlocked
        result = await self.db.execute(
            select(Achievement).where(
                Achievement.is_active == True,
                Achievement.id.notin_(unlocked_ids) if unlocked_ids else Achievement.is_active == True,
            )
        )
        candidates = list(result.scalars().all())

        newly_unlocked = []
        for ach in candidates:
            if ach.id in unlocked_ids:
                continue
            if self._check_condition(ach.condition_type, ach.condition_value, user_stats, brain_count):
                # Unlock achievement
                user_ach = UserAchievement(
                    user_id=user_id,
                    achievement_id=ach.id,
                    unlocked_at=datetime.now(timezone.utc),
                )
                self.db.add(user_ach)

                # Award XP bonus
                if ach.xp_reward > 0:
                    user_stats.total_xp += ach.xp_reward

                newly_unlocked.append(ach)

        if newly_unlocked:
            await self.db.flush()

        return newly_unlocked

    @staticmethod
    def _check_condition(
        condition_type: str,
        condition_value: int,
        user_stats: UserStats,
        brain_count: int,
    ) -> bool:
        """Check if a single achievement condition is met."""
        if condition_type == "tasks_completed":
            return user_stats.tasks_completed >= condition_value
        elif condition_type == "streak_days":
            return user_stats.current_streak >= condition_value
        elif condition_type == "brain_entries":
            return brain_count >= condition_value
        elif condition_type == "total_xp":
            return user_stats.total_xp >= condition_value
        return False
