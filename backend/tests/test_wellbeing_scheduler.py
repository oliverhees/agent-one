"""Tests for wellbeing scheduler integration."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4


class TestWellbeingSchedulerFunction:
    def test_function_exists(self):
        from app.services.scheduler import _process_wellbeing_check
        assert callable(_process_wellbeing_check)

    @pytest.mark.asyncio
    async def test_calls_wellbeing_service(self):
        from app.services.scheduler import _process_wellbeing_check
        user_id = uuid4()
        settings = {"active_modules": ["core", "wellness"]}
        with patch("app.services.scheduler.WellbeingService") as MockWS, \
             patch("app.services.scheduler.InterventionEngine") as MockIE, \
             patch("app.services.scheduler.AsyncSessionLocal") as MockSession:
            mock_db = AsyncMock()
            MockSession.return_value.__aenter__ = AsyncMock(return_value=mock_db)
            MockSession.return_value.__aexit__ = AsyncMock(return_value=False)
            MockWS.return_value.calculate_and_store = AsyncMock(return_value={"score": 50, "zone": "yellow"})
            MockIE.return_value.evaluate = AsyncMock(return_value=[])
            await _process_wellbeing_check(user_id, settings)
            MockWS.return_value.calculate_and_store.assert_called_once()

    @pytest.mark.asyncio
    async def test_skips_when_wellness_not_active(self):
        from app.services.scheduler import _process_wellbeing_check
        user_id = uuid4()
        settings = {"active_modules": ["core", "adhs"]}
        with patch("app.services.scheduler.WellbeingService") as MockWS:
            await _process_wellbeing_check(user_id, settings)
            MockWS.assert_not_called()
