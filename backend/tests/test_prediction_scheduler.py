"""Tests for prediction scheduler integration."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4


class TestPredictionScheduler:
    @pytest.mark.asyncio
    async def test_process_predictions_skipped_without_module(self):
        from app.services.scheduler import _process_predictions
        settings = {"active_modules": ["core", "adhs"]}
        await _process_predictions(uuid4(), settings)
        # Should return without error — wellness module not active

    @pytest.mark.asyncio
    async def test_process_predictions_runs_with_wellness(self):
        from app.services.scheduler import _process_predictions
        settings = {"active_modules": ["core", "adhs", "wellness"]}

        with patch("app.services.scheduler.PredictionEngine") as MockEngine:
            mock_instance = MagicMock()
            mock_instance.expire_old_predictions = AsyncMock(return_value=0)
            mock_instance.predict = AsyncMock(return_value=[])
            MockEngine.return_value = mock_instance

            await _process_predictions(uuid4(), settings)
            mock_instance.predict.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_predictions_sends_push_for_high_confidence(self):
        from app.services.scheduler import _process_predictions
        settings = {
            "active_modules": ["core", "adhs", "wellness"],
            "expo_push_token": "ExponentPushToken[test]",
        }

        with patch("app.services.scheduler.PredictionEngine") as MockEngine, \
             patch("app.services.scheduler.NotificationService") as MockNotif:
            mock_instance = MagicMock()
            mock_instance.expire_old_predictions = AsyncMock(return_value=0)
            mock_instance.predict = AsyncMock(return_value=[{
                "id": str(uuid4()),
                "pattern_type": "energy_crash",
                "confidence": 0.85,
                "predicted_for": "2026-02-15T10:00:00Z",
                "time_horizon": "24h",
                "trigger_factors": {},
                "graphiti_context": {},
                "status": "active",
            }])
            MockEngine.return_value = mock_instance
            MockNotif.send_notification = AsyncMock()

            await _process_predictions(uuid4(), settings)
            MockNotif.send_notification.assert_called_once()
