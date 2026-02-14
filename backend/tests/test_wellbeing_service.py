"""Tests for WellbeingService."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


class TestCalculateScore:
    def test_calculate_from_trends(self):
        from app.services.wellbeing import WellbeingService
        service = WellbeingService.__new__(WellbeingService)
        trends = {"avg_mood": 0.6, "avg_energy": 0.7, "avg_focus": 0.5, "total_conversations": 5}
        stats = {"tasks_completed": 10, "current_streak": 3}
        score, components = service._compute_score(trends, stats)
        assert 0 <= score <= 100
        assert "mood" in components
        assert "energy" in components
        assert "focus" in components

    def test_zone_red(self):
        from app.services.wellbeing import WellbeingService
        assert WellbeingService._zone_for_score(15) == "red"

    def test_zone_yellow(self):
        from app.services.wellbeing import WellbeingService
        assert WellbeingService._zone_for_score(45) == "yellow"

    def test_zone_green(self):
        from app.services.wellbeing import WellbeingService
        assert WellbeingService._zone_for_score(75) == "green"

    def test_zone_boundary_30(self):
        from app.services.wellbeing import WellbeingService
        assert WellbeingService._zone_for_score(30) == "red"

    def test_zone_boundary_31(self):
        from app.services.wellbeing import WellbeingService
        assert WellbeingService._zone_for_score(31) == "yellow"

    def test_zone_boundary_60(self):
        from app.services.wellbeing import WellbeingService
        assert WellbeingService._zone_for_score(60) == "yellow"

    def test_zone_boundary_61(self):
        from app.services.wellbeing import WellbeingService
        assert WellbeingService._zone_for_score(61) == "green"

    def test_all_zeros_returns_low_score(self):
        from app.services.wellbeing import WellbeingService
        service = WellbeingService.__new__(WellbeingService)
        trends = {"avg_mood": -1.0, "avg_energy": 0.0, "avg_focus": 0.0, "total_conversations": 1}
        stats = {"tasks_completed": 0, "current_streak": 0}
        score, _ = service._compute_score(trends, stats)
        assert score <= 30

    def test_all_max_returns_high_score(self):
        from app.services.wellbeing import WellbeingService
        service = WellbeingService.__new__(WellbeingService)
        trends = {"avg_mood": 1.0, "avg_energy": 1.0, "avg_focus": 1.0, "total_conversations": 10}
        stats = {"tasks_completed": 50, "current_streak": 14}
        score, _ = service._compute_score(trends, stats)
        assert score >= 70

    def test_no_data_returns_neutral_score(self):
        from app.services.wellbeing import WellbeingService
        service = WellbeingService.__new__(WellbeingService)
        trends = {"avg_mood": 0, "avg_energy": 0, "avg_focus": 0, "total_conversations": 0}
        stats = {"tasks_completed": 0, "current_streak": 0}
        score, _ = service._compute_score(trends, stats)
        assert 40 <= score <= 60


class TestGetScoreHistory:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_scores(self):
        from app.services.wellbeing import WellbeingService
        db = AsyncMock()
        db.execute = AsyncMock(return_value=MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))))
        service = WellbeingService(db)
        result = await service.get_score_history(str(uuid4()), days=7)
        assert result["scores"] == []
        assert result["trend"] == "stable"
