"""Gamification schemas for request/response validation."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class GamificationStatsResponse(BaseModel):
    """Schema for gamification stats response."""

    total_xp: int = Field(..., description="Total XP earned")
    level: int = Field(..., description="Current level")
    current_streak: int = Field(..., description="Current streak in consecutive active days")
    longest_streak: int = Field(..., description="Longest streak ever achieved")
    xp_for_next_level: int = Field(..., description="XP threshold for next level")
    progress_percent: float = Field(..., description="Progress to next level (0.0 - 100.0)")
    tasks_completed: int = Field(..., description="Total number of completed tasks")


class XPHistoryEntry(BaseModel):
    """Schema for a single day's XP history."""

    date: str = Field(..., description="Date in YYYY-MM-DD format")
    xp_earned: int = Field(..., description="XP earned on this day")
    tasks_completed: int = Field(..., description="Tasks completed on this day")


class XPHistoryResponse(BaseModel):
    """Schema for XP history response."""

    history: list[XPHistoryEntry] = Field(..., description="XP history per day (descending)")
    total_days: int = Field(..., description="Requested time period in days")


class AchievementResponse(BaseModel):
    """Schema for a single achievement response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Achievement unique identifier")
    name: str = Field(..., description="Achievement name")
    description: str = Field(..., description="Description of unlock condition")
    icon: str = Field(..., description="Icon name")
    category: str = Field(..., description="Category: task, streak, brain, social, special")
    xp_reward: int = Field(..., description="XP reward when unlocked")
    unlocked: bool = Field(..., description="Unlocked by user?")
    unlocked_at: datetime | None = Field(None, description="Unlock timestamp")


class AchievementListResponse(BaseModel):
    """Schema for achievements list response."""

    achievements: list[AchievementResponse] = Field(..., description="All available achievements")
    total_count: int = Field(..., description="Total number of achievements")
    unlocked_count: int = Field(..., description="Number of unlocked achievements")
