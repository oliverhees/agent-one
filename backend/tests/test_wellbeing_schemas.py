"""Tests for wellbeing Pydantic schemas."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.wellbeing import (
    InterventionAction,
    InterventionResponse,
    WellbeingHistoryResponse,
    WellbeingScoreResponse,
)


class TestWellbeingScoreResponse:
    """Tests for WellbeingScoreResponse schema."""

    def test_valid_creation(self):
        """Test creating a valid WellbeingScoreResponse."""
        now = datetime.now(timezone.utc)
        score = WellbeingScoreResponse(
            score=75.5,
            zone="green",
            components={"mood": 80, "energy": 70},
            calculated_at=now,
        )

        assert score.score == 75.5
        assert score.zone == "green"
        assert score.components == {"mood": 80, "energy": 70}
        assert score.calculated_at == now

    def test_score_minimum_boundary(self):
        """Test score=0 is valid."""
        now = datetime.now(timezone.utc)
        score = WellbeingScoreResponse(
            score=0,
            zone="red",
            components={},
            calculated_at=now,
        )

        assert score.score == 0

    def test_score_maximum_boundary(self):
        """Test score=100 is valid."""
        now = datetime.now(timezone.utc)
        score = WellbeingScoreResponse(
            score=100,
            zone="green",
            components={},
            calculated_at=now,
        )

        assert score.score == 100

    def test_score_out_of_range_above(self):
        """Test score > 100 raises ValidationError."""
        now = datetime.now(timezone.utc)

        with pytest.raises(ValidationError) as exc_info:
            WellbeingScoreResponse(
                score=101,
                zone="green",
                components={},
                calculated_at=now,
            )

        errors = exc_info.value.errors()
        assert any("score" in str(err["loc"]) for err in errors)
        assert any("less than or equal to 100" in str(err["msg"]) for err in errors)

    def test_score_negative_raises(self):
        """Test score < 0 raises ValidationError."""
        now = datetime.now(timezone.utc)

        with pytest.raises(ValidationError) as exc_info:
            WellbeingScoreResponse(
                score=-5,
                zone="red",
                components={},
                calculated_at=now,
            )

        errors = exc_info.value.errors()
        assert any("score" in str(err["loc"]) for err in errors)
        assert any("greater than or equal to 0" in str(err["msg"]) for err in errors)

    def test_empty_components_default(self):
        """Test components defaults to empty dict."""
        now = datetime.now(timezone.utc)
        score = WellbeingScoreResponse(
            score=50,
            zone="yellow",
            calculated_at=now,
        )

        assert score.components == {}


class TestWellbeingHistoryResponse:
    """Tests for WellbeingHistoryResponse schema."""

    def test_valid_creation(self):
        """Test creating a valid WellbeingHistoryResponse."""
        now = datetime.now(timezone.utc)
        scores = [
            WellbeingScoreResponse(score=80, zone="green", calculated_at=now),
            WellbeingScoreResponse(score=60, zone="yellow", calculated_at=now),
        ]

        history = WellbeingHistoryResponse(
            scores=scores,
            trend="declining",
            average_score=70.0,
            days=7,
        )

        assert len(history.scores) == 2
        assert history.trend == "declining"
        assert history.average_score == 70.0
        assert history.days == 7

    def test_average_score_boundaries(self):
        """Test average_score respects 0-100 boundaries."""
        history = WellbeingHistoryResponse(
            scores=[],
            trend="stable",
            average_score=0,
            days=1,
        )
        assert history.average_score == 0

        history = WellbeingHistoryResponse(
            scores=[],
            trend="stable",
            average_score=100,
            days=1,
        )
        assert history.average_score == 100

    def test_average_score_out_of_range(self):
        """Test average_score > 100 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            WellbeingHistoryResponse(
                scores=[],
                trend="stable",
                average_score=150,
                days=1,
            )

        errors = exc_info.value.errors()
        assert any("average_score" in str(err["loc"]) for err in errors)

    def test_days_minimum_boundary(self):
        """Test days >= 1."""
        history = WellbeingHistoryResponse(
            scores=[],
            trend="stable",
            average_score=50,
            days=1,
        )
        assert history.days == 1

    def test_days_zero_raises(self):
        """Test days < 1 raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            WellbeingHistoryResponse(
                scores=[],
                trend="stable",
                average_score=50,
                days=0,
            )

        errors = exc_info.value.errors()
        assert any("days" in str(err["loc"]) for err in errors)
        assert any("greater than or equal to 1" in str(err["msg"]) for err in errors)

    def test_empty_scores_default(self):
        """Test scores defaults to empty list."""
        history = WellbeingHistoryResponse(
            trend="stable",
            average_score=50,
            days=1,
        )

        assert history.scores == []


class TestInterventionResponse:
    """Tests for InterventionResponse schema."""

    def test_valid_creation(self):
        """Test creating a valid InterventionResponse."""
        intervention_id = uuid4()
        now = datetime.now(timezone.utc)

        intervention = InterventionResponse(
            id=intervention_id,
            type="proactive_check_in",
            trigger_pattern="low_wellbeing",
            message="Wie geht es dir?",
            status="pending",
            created_at=now,
        )

        assert intervention.id == intervention_id
        assert intervention.type == "proactive_check_in"
        assert intervention.trigger_pattern == "low_wellbeing"
        assert intervention.message == "Wie geht es dir?"
        assert intervention.status == "pending"
        assert intervention.created_at == now


class TestInterventionAction:
    """Tests for InterventionAction schema."""

    def test_valid_dismiss_action(self):
        """Test action='dismiss' is valid."""
        action = InterventionAction(action="dismiss")
        assert action.action == "dismiss"

    def test_valid_act_action(self):
        """Test action='act' is valid."""
        action = InterventionAction(action="act")
        assert action.action == "act"

    def test_invalid_action_raises(self):
        """Test invalid action raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            InterventionAction(action="invalid")

        errors = exc_info.value.errors()
        assert any("action" in str(err["loc"]) for err in errors)
        assert any("String should match pattern" in str(err["msg"]) for err in errors)

    def test_empty_action_raises(self):
        """Test empty action raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            InterventionAction(action="")

        errors = exc_info.value.errors()
        assert any("action" in str(err["loc"]) for err in errors)


class TestSchemaRegistration:
    """Tests for schema registration in __init__.py."""

    def test_schemas_are_importable(self):
        """Test all wellbeing schemas are importable from app.schemas."""
        from app.schemas import (
            InterventionAction,
            InterventionResponse,
            WellbeingHistoryResponse,
            WellbeingScoreResponse,
        )

        # If imports work, test passes
        assert WellbeingScoreResponse is not None
        assert WellbeingHistoryResponse is not None
        assert InterventionResponse is not None
        assert InterventionAction is not None
