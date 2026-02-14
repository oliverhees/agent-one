"""Tests for BriefingService."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import date, datetime, timezone
from uuid import uuid4


class TestPrioritizeTasks:
    def test_sorts_by_priority(self):
        from app.services.briefing import BriefingService
        tasks = [
            MagicMock(id=uuid4(), title="Low", priority=MagicMock(value="low"), due_date=None, estimated_minutes=30, status=MagicMock(value="open")),
            MagicMock(id=uuid4(), title="Urgent", priority=MagicMock(value="urgent"), due_date=None, estimated_minutes=15, status=MagicMock(value="open")),
            MagicMock(id=uuid4(), title="High", priority=MagicMock(value="high"), due_date=None, estimated_minutes=45, status=MagicMock(value="open")),
        ]
        result = BriefingService._prioritize_tasks(tasks, max_tasks=3)
        assert result[0]["title"] == "Urgent"
        assert result[1]["title"] == "High"
        assert result[2]["title"] == "Low"

    def test_respects_max_tasks(self):
        from app.services.briefing import BriefingService
        tasks = [
            MagicMock(id=uuid4(), title=f"Task {i}", priority=MagicMock(value="medium"), due_date=None, estimated_minutes=30, status=MagicMock(value="open"))
            for i in range(10)
        ]
        result = BriefingService._prioritize_tasks(tasks, max_tasks=3)
        assert len(result) == 3

    def test_empty_tasks(self):
        from app.services.briefing import BriefingService
        result = BriefingService._prioritize_tasks([], max_tasks=3)
        assert result == []

    def test_due_date_boosts_priority(self):
        from app.services.briefing import BriefingService
        from datetime import timedelta
        soon = datetime.now(timezone.utc) + timedelta(hours=2)
        later = datetime.now(timezone.utc) + timedelta(days=5)
        tasks = [
            MagicMock(id=uuid4(), title="Later", priority=MagicMock(value="medium"), due_date=later, estimated_minutes=30, status=MagicMock(value="open")),
            MagicMock(id=uuid4(), title="Soon", priority=MagicMock(value="medium"), due_date=soon, estimated_minutes=30, status=MagicMock(value="open")),
        ]
        result = BriefingService._prioritize_tasks(tasks, max_tasks=3)
        assert result[0]["title"] == "Soon"


class TestGenerateBriefingContent:
    def test_builds_prompt_context(self):
        from app.services.briefing import BriefingService
        tasks = [{"task_id": "a", "title": "Test", "priority": "high", "reason": None}]
        wellbeing = {"score": 72, "zone": "green", "components": {}}
        trends = {"avg_mood": 0.3, "avg_energy": 0.6, "avg_focus": 0.5, "mood_trend": "rising"}
        ctx = BriefingService._build_prompt_context(
            display_name="Oliver",
            tasks=tasks,
            wellbeing=wellbeing,
            trends=trends,
        )
        assert "Oliver" in ctx
        assert "72" in ctx
        assert "Test" in ctx


@pytest.mark.asyncio
class TestGetTodayBriefing:
    async def test_returns_none_if_no_briefing(self):
        from app.services.briefing import BriefingService
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        service = BriefingService(mock_db)
        result = await service.get_today_briefing(str(uuid4()))
        assert result is None


@pytest.mark.asyncio
class TestMarkAsRead:
    async def test_marks_briefing_read(self):
        from app.services.briefing import BriefingService
        mock_db = AsyncMock()
        mock_briefing = MagicMock()
        mock_briefing.status = "generated"
        mock_briefing.read_at = None
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_briefing
        mock_db.execute = AsyncMock(return_value=mock_result)

        service = BriefingService(mock_db)
        result = await service.mark_as_read(str(uuid4()), str(uuid4()))
        assert result is True
