"""Gamification endpoint tests."""

import math
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.services.gamification import GamificationService
from app.models.achievement import Achievement, AchievementCategory


# ---------------------------------------------------------------------------
# Achievement seed data (matches migration 003)
# ---------------------------------------------------------------------------

SEED_ACHIEVEMENTS = [
    {"name": "First Steps", "description": "Erledige deinen ersten Task.", "icon": "target", "category": AchievementCategory.TASK, "condition_type": "tasks_completed", "condition_value": 1, "xp_reward": 50, "is_active": True},
    {"name": "Getting Things Done", "description": "Erledige 10 Tasks.", "icon": "check", "category": AchievementCategory.TASK, "condition_type": "tasks_completed", "condition_value": 10, "xp_reward": 100, "is_active": True},
    {"name": "Century Club", "description": "Erledige 100 Tasks.", "icon": "100", "category": AchievementCategory.TASK, "condition_type": "tasks_completed", "condition_value": 100, "xp_reward": 500, "is_active": True},
    {"name": "Week Warrior", "description": "Halte eine Streak von 7 Tagen.", "icon": "fire", "category": AchievementCategory.STREAK, "condition_type": "streak_days", "condition_value": 7, "xp_reward": 150, "is_active": True},
    {"name": "Dedicated", "description": "Halte eine Streak von 30 Tagen.", "icon": "star", "category": AchievementCategory.STREAK, "condition_type": "streak_days", "condition_value": 30, "xp_reward": 500, "is_active": True},
    {"name": "Brain Scholar", "description": "Erstelle 10 Brain-Eintraege.", "icon": "brain", "category": AchievementCategory.BRAIN, "condition_type": "brain_entries", "condition_value": 10, "xp_reward": 100, "is_active": True},
    {"name": "Knowledge Base", "description": "Erstelle 50 Brain-Eintraege.", "icon": "books", "category": AchievementCategory.BRAIN, "condition_type": "brain_entries", "condition_value": 50, "xp_reward": 300, "is_active": True},
    {"name": "Speed Demon", "description": "Erledige einen Task in unter 5 Minuten.", "icon": "lightning", "category": AchievementCategory.SPECIAL, "condition_type": "task_under_5min", "condition_value": 1, "xp_reward": 75, "is_active": True},
]

TEST_DATABASE_URL = "postgresql+asyncpg://alice:alice_dev_123@localhost:5432/alice_test"


async def _seed_achievements():
    """Seed achievements using a short-lived connection that's closed immediately."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        for data in SEED_ACHIEVEMENTS:
            session.add(Achievement(**data))
        await session.commit()
    await engine.dispose()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _create_and_complete_task(
    client: AsyncClient,
    title: str = "Task",
    priority: str = "medium",
    due_date: str | None = None,
) -> dict:
    """Create a task and complete it; return the complete-response JSON."""
    payload: dict = {"title": title, "priority": priority}
    if due_date:
        payload["due_date"] = due_date
    r = await client.post("/api/v1/tasks/", json=payload)
    assert r.status_code == 201
    task_id = r.json()["id"]
    cr = await client.post(f"/api/v1/tasks/{task_id}/complete")
    assert cr.status_code == 200
    return cr.json()


# ===========================================================================
# Gamification Stats
# ===========================================================================

class TestGamificationStats:
    """Tests for GET /api/v1/gamification/stats."""

    async def test_stats_default_new_user(self, authenticated_client: AsyncClient, test_user):
        """New user should get default stats (0 XP, level 1, streak 0)."""
        response = await authenticated_client.get("/api/v1/gamification/stats")

        assert response.status_code == 200
        data = response.json()

        assert data["total_xp"] == 0
        assert data["level"] == 1
        assert data["current_streak"] == 0
        assert data["longest_streak"] == 0
        assert data["tasks_completed"] == 0
        assert data["xp_for_next_level"] == 400  # ((1+1)**2)*100
        assert data["progress_percent"] == 0.0

    async def test_stats_after_task_complete(self, authenticated_client: AsyncClient, test_user):
        """Stats should update after completing a task."""
        await _create_and_complete_task(authenticated_client, priority="medium")

        response = await authenticated_client.get("/api/v1/gamification/stats")

        assert response.status_code == 200
        data = response.json()

        assert data["total_xp"] > 0
        assert data["tasks_completed"] == 1
        assert data["current_streak"] >= 1

    async def test_stats_xp_accumulates(self, authenticated_client: AsyncClient, test_user):
        """XP should accumulate over multiple completed tasks."""
        await _create_and_complete_task(authenticated_client, priority="low")
        await _create_and_complete_task(authenticated_client, priority="low")

        response = await authenticated_client.get("/api/v1/gamification/stats")
        data = response.json()

        assert data["tasks_completed"] == 2
        # Each low = 10 base, + streak bonus on second
        assert data["total_xp"] > 10

    async def test_stats_unauthorized(self, client: AsyncClient):
        """Stats without auth should return 403."""
        response = await client.get("/api/v1/gamification/stats")
        assert response.status_code == 403


# ===========================================================================
# Level formula unit tests
# ===========================================================================

class TestLevelFormula:
    """Tests for the level calculation formula: floor(sqrt(total_xp / 100))."""

    def test_zero_xp(self):
        assert GamificationService.calculate_level(0) == 1

    def test_negative_xp(self):
        assert GamificationService.calculate_level(-50) == 1

    def test_99_xp(self):
        """99 XP -> sqrt(0.99) = 0.99 -> floor = 0 -> min 1."""
        assert GamificationService.calculate_level(99) == 1

    def test_100_xp(self):
        """100 XP -> sqrt(1) = 1 -> level 1."""
        assert GamificationService.calculate_level(100) == 1

    def test_400_xp(self):
        """400 XP -> sqrt(4) = 2 -> level 2."""
        assert GamificationService.calculate_level(400) == 2

    def test_900_xp(self):
        """900 XP -> sqrt(9) = 3 -> level 3."""
        assert GamificationService.calculate_level(900) == 3

    def test_10000_xp(self):
        """10000 XP -> sqrt(100) = 10 -> level 10."""
        assert GamificationService.calculate_level(10000) == 10

    def test_250_xp(self):
        """250 XP -> sqrt(2.5) = 1.58 -> floor = 1."""
        assert GamificationService.calculate_level(250) == 1


# ===========================================================================
# XP Calculation per Priority
# ===========================================================================

class TestXPCalculation:
    """Tests for XP earned based on priority."""

    async def test_low_priority_xp(self, authenticated_client: AsyncClient, test_user):
        """Low priority tasks give 10 base XP (+ streak bonus)."""
        result = await _create_and_complete_task(authenticated_client, priority="low")
        # First task: 10 base + streak bonus (streak becomes 1 -> +25% = 2)
        assert result["xp_earned"] >= 10

    async def test_medium_priority_xp(self, authenticated_client: AsyncClient, test_user):
        """Medium priority tasks give 25 base XP (+ streak bonus)."""
        result = await _create_and_complete_task(authenticated_client, priority="medium")
        assert result["xp_earned"] >= 25

    async def test_high_priority_xp(self, authenticated_client: AsyncClient, test_user):
        """High priority tasks give 50 base XP (+ streak bonus)."""
        result = await _create_and_complete_task(authenticated_client, priority="high")
        assert result["xp_earned"] >= 50

    async def test_urgent_priority_xp(self, authenticated_client: AsyncClient, test_user):
        """Urgent priority tasks give 100 base XP (+ streak bonus)."""
        result = await _create_and_complete_task(authenticated_client, priority="urgent")
        assert result["xp_earned"] >= 100

    async def test_on_time_bonus(self, authenticated_client: AsyncClient, test_user):
        """Completing before due_date gives +50% bonus."""
        future = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        result = await _create_and_complete_task(
            authenticated_client, priority="low", due_date=future,
        )
        # low base = 10, on-time +50% = 15, then streak bonus
        assert result["xp_earned"] >= 15


# ===========================================================================
# XP History
# ===========================================================================

class TestXPHistory:
    """Tests for GET /api/v1/gamification/history."""

    async def test_history_empty(self, authenticated_client: AsyncClient, test_user):
        """Empty history for new user."""
        response = await authenticated_client.get("/api/v1/gamification/history")

        assert response.status_code == 200
        data = response.json()

        assert data["history"] == []
        assert data["total_days"] == 30

    async def test_history_after_complete(self, authenticated_client: AsyncClient, test_user):
        """History should show today's entry after completing a task."""
        await _create_and_complete_task(authenticated_client)

        response = await authenticated_client.get("/api/v1/gamification/history")

        assert response.status_code == 200
        data = response.json()

        assert len(data["history"]) == 1
        entry = data["history"][0]
        assert entry["xp_earned"] > 0
        assert entry["tasks_completed"] == 1

    async def test_history_days_param(self, authenticated_client: AsyncClient, test_user):
        """Custom days parameter should be reflected in total_days."""
        response = await authenticated_client.get("/api/v1/gamification/history?days=7")

        assert response.status_code == 200
        data = response.json()
        assert data["total_days"] == 7

    async def test_history_unauthorized(self, client: AsyncClient):
        """History without auth should return 403."""
        response = await client.get("/api/v1/gamification/history")
        assert response.status_code == 403


# ===========================================================================
# Achievements
# ===========================================================================

class TestAchievements:
    """Tests for GET /api/v1/gamification/achievements."""

    async def test_achievements_list_seeded(self, authenticated_client: AsyncClient, test_user):
        """Should return the 8 seeded achievements."""
        await _seed_achievements()

        response = await authenticated_client.get("/api/v1/gamification/achievements")

        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == 8
        assert data["unlocked_count"] == 0
        assert len(data["achievements"]) == 8

    async def test_achievements_unlock_first_steps(self, authenticated_client: AsyncClient, test_user):
        """'First Steps' achievement should unlock after completing 1 task."""
        await _seed_achievements()

        await _create_and_complete_task(authenticated_client)

        response = await authenticated_client.get("/api/v1/gamification/achievements")

        assert response.status_code == 200
        data = response.json()

        assert data["unlocked_count"] >= 1

        first_steps = next(
            (a for a in data["achievements"] if a["name"] == "First Steps"), None
        )
        assert first_steps is not None
        assert first_steps["unlocked"] is True
        assert first_steps["unlocked_at"] is not None

    async def test_achievements_no_double_unlock(self, authenticated_client: AsyncClient, test_user):
        """Completing more tasks should not re-unlock the same achievement."""
        await _seed_achievements()

        await _create_and_complete_task(authenticated_client)
        await _create_and_complete_task(authenticated_client, title="Task 2")

        response = await authenticated_client.get("/api/v1/gamification/achievements")
        data = response.json()

        first_steps = [a for a in data["achievements"] if a["name"] == "First Steps"]
        assert len(first_steps) == 1  # only appears once

    async def test_achievements_unauthorized(self, client: AsyncClient):
        """Achievements without auth should return 403."""
        response = await client.get("/api/v1/gamification/achievements")
        assert response.status_code == 403

    async def test_achievements_structure(self, authenticated_client: AsyncClient, test_user):
        """Each achievement should have the required fields."""
        await _seed_achievements()

        response = await authenticated_client.get("/api/v1/gamification/achievements")
        data = response.json()

        for ach in data["achievements"]:
            assert "id" in ach
            assert "name" in ach
            assert "description" in ach
            assert "icon" in ach
            assert "category" in ach
            assert "xp_reward" in ach
            assert "unlocked" in ach
            assert "unlocked_at" in ach
