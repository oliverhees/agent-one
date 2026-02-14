"""Tests for briefing scheduler integration."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4


class TestBriefingSchedulerFunction:
    def test_function_exists(self):
        from app.services.scheduler import _process_morning_briefing
        assert callable(_process_morning_briefing)

    @pytest.mark.asyncio
    async def test_generates_briefing_at_configured_time(self):
        from app.services.scheduler import _process_morning_briefing
        user_id = uuid4()
        settings = {
            "active_modules": ["core", "productivity"],
            "morning_briefing": True,
            "briefing_time": "07:00",
            "display_name": "Oliver",
            "max_daily_tasks": 3,
        }
        with patch("app.services.scheduler.BriefingService") as MockBS, \
             patch("app.services.scheduler.AsyncSessionLocal") as MockSession, \
             patch("app.services.scheduler._is_near_reminder_time", return_value=True):
            mock_db = AsyncMock()
            MockSession.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            MockSession.return_value.__aexit__ = AsyncMock(return_value=False)
            MockBS.return_value.get_today_briefing = AsyncMock(return_value=None)
            MockBS.return_value.generate_briefing = AsyncMock(
                return_value={"content": "Guten Morgen!", "id": "abc"}
            )
            await _process_morning_briefing(user_id, settings)
            MockBS.return_value.generate_briefing.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_when_productivity_not_active(self):
        from app.services.scheduler import _process_morning_briefing
        user_id = uuid4()
        settings = {"active_modules": ["core", "adhs"], "morning_briefing": True}
        with patch("app.services.scheduler.BriefingService") as MockBS:
            await _process_morning_briefing(user_id, settings)
            MockBS.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_briefing_disabled(self):
        from app.services.scheduler import _process_morning_briefing
        user_id = uuid4()
        settings = {
            "active_modules": ["core", "productivity"],
            "morning_briefing": False,
        }
        with patch("app.services.scheduler.BriefingService") as MockBS:
            await _process_morning_briefing(user_id, settings)
            MockBS.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_already_generated(self):
        from app.services.scheduler import _process_morning_briefing
        user_id = uuid4()
        settings = {
            "active_modules": ["core", "productivity"],
            "morning_briefing": True,
            "briefing_time": "07:00",
        }
        with patch("app.services.scheduler.BriefingService") as MockBS, \
             patch("app.services.scheduler.AsyncSessionLocal") as MockSession, \
             patch("app.services.scheduler._is_near_reminder_time", return_value=True):
            mock_db = AsyncMock()
            MockSession.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            MockSession.return_value.__aexit__ = AsyncMock(return_value=False)
            MockBS.return_value.get_today_briefing = AsyncMock(
                return_value={"id": "exists", "content": "Already done"}
            )
            await _process_morning_briefing(user_id, settings)
            MockBS.return_value.generate_briefing.assert_not_called()
