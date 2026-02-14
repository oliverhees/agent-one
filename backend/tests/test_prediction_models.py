"""Tests for PredictedPattern model."""
import pytest
from datetime import datetime, timedelta, timezone

from app.models.predicted_pattern import PredictedPattern, PredictionStatus
from app.models.user import User


class TestPredictedPatternModel:
    def test_prediction_status_enum_values(self):
        """Test that PredictionStatus enum has correct values."""
        assert PredictionStatus.ACTIVE == "active"
        assert PredictionStatus.CONFIRMED == "confirmed"
        assert PredictionStatus.AVOIDED == "avoided"
        assert PredictionStatus.EXPIRED == "expired"

    @pytest.mark.asyncio
    async def test_create_predicted_pattern(self, test_db):
        """Test creating a predicted pattern."""
        # Create test user
        user = User(
            email="test@example.com",
            password_hash="hashed",
            display_name="Test User",
        )
        test_db.add(user)
        await test_db.flush()

        # Create prediction
        prediction = PredictedPattern(
            user_id=user.id,
            pattern_type="energy_crash",
            confidence=0.78,
            predicted_for=datetime.now(timezone.utc) + timedelta(hours=24),
            time_horizon="24h",
            trigger_factors={"energy_trend": "declining", "avg_energy": 0.32},
            graphiti_context={},
            status=PredictionStatus.ACTIVE,
        )
        test_db.add(prediction)
        await test_db.flush()

        assert prediction.id is not None
        assert prediction.pattern_type == "energy_crash"
        assert prediction.confidence == 0.78
        assert prediction.time_horizon == "24h"
        assert prediction.status == "active"
        assert prediction.resolved_at is None

    @pytest.mark.asyncio
    async def test_prediction_user_relationship(self, test_db):
        """Test that prediction-user relationship works."""
        # Create test user
        user = User(
            email="test2@example.com",
            password_hash="hashed",
            display_name="Test User 2",
        )
        test_db.add(user)
        await test_db.flush()

        # Create prediction
        prediction = PredictedPattern(
            user_id=user.id,
            pattern_type="procrastination",
            confidence=0.65,
            predicted_for=datetime.now(timezone.utc) + timedelta(days=3),
            time_horizon="3d",
            trigger_factors={},
            graphiti_context={},
            status=PredictionStatus.ACTIVE,
        )
        test_db.add(prediction)
        await test_db.flush()

        # Refresh to load relationship
        await test_db.refresh(prediction, ["user"])

        assert prediction.user is not None
        assert prediction.user.id == user.id

    @pytest.mark.asyncio
    async def test_prediction_repr(self, test_db):
        """Test __repr__ method."""
        # Create test user
        user = User(
            email="test3@example.com",
            password_hash="hashed",
            display_name="Test User 3",
        )
        test_db.add(user)
        await test_db.flush()

        # Create prediction
        prediction = PredictedPattern(
            user_id=user.id,
            pattern_type="hyperfocus",
            confidence=0.85,
            predicted_for=datetime.now(timezone.utc) + timedelta(hours=12),
            time_horizon="24h",
            trigger_factors={},
            graphiti_context={},
            status=PredictionStatus.ACTIVE,
        )
        test_db.add(prediction)
        await test_db.flush()

        repr_str = repr(prediction)
        assert "PredictedPattern" in repr_str
        assert "hyperfocus" in repr_str
