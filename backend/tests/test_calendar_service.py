"""Tests for CalendarService."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime, timezone, timedelta

from app.services.calendar import CalendarService


class TestCalendarService:
    @pytest.mark.asyncio
    async def test_get_today_events_empty(self, test_db):
        service = CalendarService(test_db)
        events = await service.get_today_events("00000000-0000-0000-0000-000000000000")
        assert events == []

    @pytest.mark.asyncio
    async def test_get_upcoming_events_empty(self, test_db):
        service = CalendarService(test_db)
        events = await service.get_upcoming_events("00000000-0000-0000-0000-000000000000")
        assert events == []

    @pytest.mark.asyncio
    async def test_disconnect_no_credentials(self, test_db):
        service = CalendarService(test_db)
        # Should not raise even if no credentials exist
        await service.disconnect("00000000-0000-0000-0000-000000000000")

    def test_build_google_auth_url(self):
        url = CalendarService.build_google_auth_url("http://localhost/callback", "test-state")
        assert "accounts.google.com" in url
        assert "test-state" in url
