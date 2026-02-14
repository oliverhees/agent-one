"""Tests for Phase 10 scheduler integration."""
import pytest
from unittest.mock import patch, AsyncMock


class TestCalendarSyncScheduler:
    @pytest.mark.asyncio
    async def test_calendar_sync_skipped_without_integrations_module(self):
        from app.services.scheduler import _process_calendar_sync
        settings = {"active_modules": ["core", "adhs"]}
        await _process_calendar_sync("00000000-0000-0000-0000-000000000000", settings)
        # No error, just skipped

    @pytest.mark.asyncio
    async def test_calendar_sync_skipped_without_credentials(self):
        from app.services.scheduler import _process_calendar_sync
        settings = {"active_modules": ["core", "integrations"]}
        await _process_calendar_sync("00000000-0000-0000-0000-000000000000", settings)


class TestReminderScheduler:
    @pytest.mark.asyncio
    async def test_reminders_skipped_without_integrations_module(self):
        from app.services.scheduler import _process_reminders
        settings = {"active_modules": ["core", "adhs"]}
        await _process_reminders("00000000-0000-0000-0000-000000000000", settings)
