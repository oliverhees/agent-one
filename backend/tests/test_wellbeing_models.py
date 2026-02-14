"""Tests for WellbeingScore and Intervention models."""

import pytest
from uuid import uuid4
from sqlalchemy import select

from app.models.wellbeing_score import WellbeingScore, WellbeingZone
from app.models.intervention import Intervention, InterventionType, InterventionStatus
from app.models.user import User


class TestWellbeingZoneEnum:
    """Tests for WellbeingZone enum."""

    def test_wellbeing_zone_values(self):
        """Test that WellbeingZone has correct values."""
        assert WellbeingZone.RED.value == "red"
        assert WellbeingZone.YELLOW.value == "yellow"
        assert WellbeingZone.GREEN.value == "green"

    def test_wellbeing_zone_str_inheritance(self):
        """Test that WellbeingZone inherits from str."""
        assert isinstance(WellbeingZone.RED, str)


class TestInterventionTypeEnum:
    """Tests for InterventionType enum."""

    def test_intervention_type_values(self):
        """Test that InterventionType has all required values."""
        assert InterventionType.HYPERFOCUS.value == "hyperfocus"
        assert InterventionType.PROCRASTINATION.value == "procrastination"
        assert InterventionType.DECISION_FATIGUE.value == "decision_fatigue"
        assert InterventionType.TRANSITION.value == "transition"
        assert InterventionType.ENERGY_CRASH.value == "energy_crash"
        assert InterventionType.SLEEP_DISRUPTION.value == "sleep_disruption"
        assert InterventionType.SOCIAL_MASKING.value == "social_masking"

    def test_intervention_type_str_inheritance(self):
        """Test that InterventionType inherits from str."""
        assert isinstance(InterventionType.HYPERFOCUS, str)


class TestInterventionStatusEnum:
    """Tests for InterventionStatus enum."""

    def test_intervention_status_values(self):
        """Test that InterventionStatus has correct values."""
        assert InterventionStatus.PENDING.value == "pending"
        assert InterventionStatus.DISMISSED.value == "dismissed"
        assert InterventionStatus.ACTED.value == "acted"

    def test_intervention_status_str_inheritance(self):
        """Test that InterventionStatus inherits from str."""
        assert isinstance(InterventionStatus.PENDING, str)


@pytest.mark.asyncio
class TestWellbeingScoreModel:
    """Tests for WellbeingScore model."""

    async def test_create_wellbeing_score(self, test_db):
        """Test creating a WellbeingScore instance."""
        # Create test user
        user = User(
            email="wellbeing@example.com",
            password_hash="hashed",
            display_name="Wellbeing Test User",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        # Create wellbeing score
        score = WellbeingScore(
            user_id=user.id,
            score=0.75,
            zone=WellbeingZone.GREEN,
            components={
                "energy": 0.8,
                "focus": 0.7,
                "stress": 0.3,
            },
        )
        test_db.add(score)
        await test_db.commit()
        await test_db.refresh(score)

        assert score.id is not None
        assert score.user_id == user.id
        assert score.score == 0.75
        assert score.zone == WellbeingZone.GREEN
        assert score.components["energy"] == 0.8
        assert score.created_at is not None
        assert score.updated_at is not None

    async def test_wellbeing_score_requires_user_id(self, test_db):
        """Test that WellbeingScore requires a valid user_id."""
        score = WellbeingScore(
            user_id=uuid4(),  # Non-existent user
            score=0.5,
            zone=WellbeingZone.YELLOW,
            components={},
        )
        test_db.add(score)

        with pytest.raises(Exception):  # Foreign key constraint violation
            await test_db.commit()

    async def test_wellbeing_score_cascade_delete(self, test_db):
        """Test that WellbeingScore is deleted when user is deleted."""
        # Create user and score
        user = User(
            email="cascade@example.com",
            password_hash="hashed",
            display_name="Cascade Test User",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        score = WellbeingScore(
            user_id=user.id,
            score=0.5,
            zone=WellbeingZone.YELLOW,
            components={},
        )
        test_db.add(score)
        await test_db.commit()
        score_id = score.id

        # Delete user
        await test_db.delete(user)
        await test_db.commit()

        # Check that score is also deleted
        result = await test_db.execute(
            select(WellbeingScore).where(WellbeingScore.id == score_id)
        )
        assert result.scalar_one_or_none() is None

    async def test_wellbeing_score_relationship(self, test_db):
        """Test relationship between WellbeingScore and User."""
        user = User(
            email="relation@example.com",
            password_hash="hashed",
            display_name="Relation Test User",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        score = WellbeingScore(
            user_id=user.id,
            score=0.8,
            zone=WellbeingZone.GREEN,
            components={"test": 0.8},
        )
        test_db.add(score)
        await test_db.commit()
        await test_db.refresh(score)

        # Load relationship
        result = await test_db.execute(
            select(WellbeingScore).where(WellbeingScore.id == score.id)
        )
        loaded_score = result.scalar_one()
        assert loaded_score.user.id == user.id
        assert loaded_score.user.email == "relation@example.com"


@pytest.mark.asyncio
class TestInterventionModel:
    """Tests for Intervention model."""

    async def test_create_intervention(self, test_db):
        """Test creating an Intervention instance."""
        # Create test user
        user = User(
            email="intervention@example.com",
            password_hash="hashed",
            display_name="Intervention Test User",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        # Create intervention
        intervention = Intervention(
            user_id=user.id,
            type=InterventionType.HYPERFOCUS,
            trigger_pattern="3h_no_break",
            message="Hey, you've been focused for 3 hours. Time for a break!",
            status=InterventionStatus.PENDING,
        )
        test_db.add(intervention)
        await test_db.commit()
        await test_db.refresh(intervention)

        assert intervention.id is not None
        assert intervention.user_id == user.id
        assert intervention.type == InterventionType.HYPERFOCUS
        assert intervention.trigger_pattern == "3h_no_break"
        assert intervention.message == "Hey, you've been focused for 3 hours. Time for a break!"
        assert intervention.status == InterventionStatus.PENDING
        assert intervention.created_at is not None
        assert intervention.updated_at is not None

    async def test_intervention_default_status(self, test_db):
        """Test that Intervention has default status of pending."""
        user = User(
            email="default@example.com",
            password_hash="hashed",
            display_name="Default Test User",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        intervention = Intervention(
            user_id=user.id,
            type=InterventionType.PROCRASTINATION,
            trigger_pattern="task_delay",
            message="Let's tackle that task!",
        )
        test_db.add(intervention)
        await test_db.commit()
        await test_db.refresh(intervention)

        assert intervention.status == InterventionStatus.PENDING

    async def test_intervention_requires_user_id(self, test_db):
        """Test that Intervention requires a valid user_id."""
        intervention = Intervention(
            user_id=uuid4(),  # Non-existent user
            type=InterventionType.DECISION_FATIGUE,
            trigger_pattern="many_decisions",
            message="Time to simplify!",
        )
        test_db.add(intervention)

        with pytest.raises(Exception):  # Foreign key constraint violation
            await test_db.commit()

    async def test_intervention_cascade_delete(self, test_db):
        """Test that Intervention is deleted when user is deleted."""
        # Create user and intervention
        user = User(
            email="cascade_intervention@example.com",
            password_hash="hashed",
            display_name="Cascade Intervention User",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        intervention = Intervention(
            user_id=user.id,
            type=InterventionType.ENERGY_CRASH,
            trigger_pattern="low_energy",
            message="Energy boost time!",
        )
        test_db.add(intervention)
        await test_db.commit()
        intervention_id = intervention.id

        # Delete user
        await test_db.delete(user)
        await test_db.commit()

        # Check that intervention is also deleted
        result = await test_db.execute(
            select(Intervention).where(Intervention.id == intervention_id)
        )
        assert result.scalar_one_or_none() is None

    async def test_intervention_relationship(self, test_db):
        """Test relationship between Intervention and User."""
        user = User(
            email="relation_intervention@example.com",
            password_hash="hashed",
            display_name="Relation Intervention User",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        intervention = Intervention(
            user_id=user.id,
            type=InterventionType.TRANSITION,
            trigger_pattern="context_switch",
            message="Take a moment to transition.",
        )
        test_db.add(intervention)
        await test_db.commit()
        await test_db.refresh(intervention)

        # Load relationship
        result = await test_db.execute(
            select(Intervention).where(Intervention.id == intervention.id)
        )
        loaded_intervention = result.scalar_one()
        assert loaded_intervention.user.id == user.id
        assert loaded_intervention.user.email == "relation_intervention@example.com"

    async def test_intervention_status_update(self, test_db):
        """Test updating intervention status."""
        user = User(
            email="status_update@example.com",
            password_hash="hashed",
            display_name="Status Update User",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        intervention = Intervention(
            user_id=user.id,
            type=InterventionType.SLEEP_DISRUPTION,
            trigger_pattern="late_activity",
            message="Time to wind down!",
            status=InterventionStatus.PENDING,
        )
        test_db.add(intervention)
        await test_db.commit()
        await test_db.refresh(intervention)

        # Update status
        intervention.status = InterventionStatus.ACTED
        await test_db.commit()
        await test_db.refresh(intervention)

        assert intervention.status == InterventionStatus.ACTED
