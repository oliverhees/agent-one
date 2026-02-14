"""Tests for Briefing DB model."""

import pytest
from uuid import uuid4
from sqlalchemy import select

from app.models.user import User


class TestBriefingModelImport:
    """Tests for Briefing model imports."""

    def test_briefing_model_importable(self):
        """Test that Briefing model can be imported."""
        from app.models.briefing import Briefing
        assert Briefing is not None

    def test_briefing_status_enum(self):
        """Test BriefingStatus enum values."""
        from app.models.briefing import BriefingStatus
        assert BriefingStatus.GENERATED == "generated"
        assert BriefingStatus.DELIVERED == "delivered"
        assert BriefingStatus.READ == "read"

    def test_briefing_status_str_inheritance(self):
        """Test that BriefingStatus inherits from str."""
        from app.models.briefing import BriefingStatus
        assert isinstance(BriefingStatus.GENERATED, str)

    def test_briefing_has_tablename(self):
        """Test that Briefing has correct tablename."""
        from app.models.briefing import Briefing
        assert Briefing.__tablename__ == "briefings"

    def test_briefing_in_models_init(self):
        """Test that Briefing is exported from models package."""
        from app.models import Briefing
        assert Briefing is not None

    def test_briefing_status_in_models_init(self):
        """Test that BriefingStatus is exported from models package."""
        from app.models import BriefingStatus
        assert BriefingStatus is not None


class TestBriefingModelFields:
    """Tests for Briefing model columns."""

    def test_has_user_id_column(self):
        from app.models.briefing import Briefing
        assert hasattr(Briefing, "user_id")

    def test_has_date_column(self):
        from app.models.briefing import Briefing
        assert hasattr(Briefing, "briefing_date")

    def test_has_content_column(self):
        from app.models.briefing import Briefing
        assert hasattr(Briefing, "content")

    def test_has_tasks_suggested_column(self):
        from app.models.briefing import Briefing
        assert hasattr(Briefing, "tasks_suggested")

    def test_has_wellbeing_snapshot_column(self):
        from app.models.briefing import Briefing
        assert hasattr(Briefing, "wellbeing_snapshot")

    def test_has_status_column(self):
        from app.models.briefing import Briefing
        assert hasattr(Briefing, "status")

    def test_has_read_at_column(self):
        from app.models.briefing import Briefing
        assert hasattr(Briefing, "read_at")


@pytest.mark.asyncio
class TestBriefingCRUD:
    """Tests for Briefing CRUD operations."""

    async def test_create_briefing(self, test_db):
        """Test creating a Briefing instance."""
        from app.models.briefing import Briefing, BriefingStatus
        from datetime import date

        # Create test user directly in DB
        user = User(
            email="briefing@example.com",
            password_hash="hashed",
            display_name="Briefing Test User",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        briefing = Briefing(
            user_id=user.id,
            briefing_date=date.today(),
            content="Guten Morgen! Dein Wellbeing-Score ist 72/100.",
            tasks_suggested=[
                {"task_id": "abc", "title": "Wichtige Aufgabe", "priority": "high"},
            ],
            wellbeing_snapshot={"score": 72, "zone": "green"},
            status=BriefingStatus.GENERATED,
        )
        test_db.add(briefing)
        await test_db.commit()
        await test_db.refresh(briefing)

        assert briefing.id is not None
        assert briefing.user_id == user.id
        assert briefing.status == BriefingStatus.GENERATED
        assert briefing.read_at is None
        assert briefing.tasks_suggested[0]["title"] == "Wichtige Aufgabe"
        assert briefing.wellbeing_snapshot["score"] == 72
        assert briefing.created_at is not None
        assert briefing.updated_at is not None

    async def test_briefing_default_status(self, test_db):
        """Test that Briefing has default status of generated."""
        from app.models.briefing import Briefing, BriefingStatus
        from datetime import date

        user = User(
            email="default_briefing@example.com",
            password_hash="hashed",
            display_name="Default Briefing User",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        briefing = Briefing(
            user_id=user.id,
            briefing_date=date.today(),
            content="Test briefing content",
            tasks_suggested=[],
            wellbeing_snapshot={},
        )
        test_db.add(briefing)
        await test_db.commit()
        await test_db.refresh(briefing)

        assert briefing.status == BriefingStatus.GENERATED

    async def test_briefing_requires_user_id(self, test_db):
        """Test that Briefing requires a valid user_id."""
        from app.models.briefing import Briefing
        from datetime import date

        briefing = Briefing(
            user_id=uuid4(),  # Non-existent user
            briefing_date=date.today(),
            content="Test",
            tasks_suggested=[],
            wellbeing_snapshot={},
        )
        test_db.add(briefing)

        with pytest.raises(Exception):  # Foreign key constraint violation
            await test_db.commit()

    async def test_cascade_delete(self, test_db):
        """Test that Briefing is deleted when user is deleted."""
        from app.models.briefing import Briefing
        from datetime import date

        user = User(
            email="cascade_briefing@example.com",
            password_hash="hashed",
            display_name="Cascade Briefing User",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        briefing = Briefing(
            user_id=user.id,
            briefing_date=date.today(),
            content="Test briefing",
            tasks_suggested=[],
            wellbeing_snapshot={},
        )
        test_db.add(briefing)
        await test_db.commit()
        briefing_id = briefing.id

        # Delete user
        await test_db.delete(user)
        await test_db.commit()

        # Check that briefing is also deleted
        result = await test_db.execute(
            select(Briefing).where(Briefing.id == briefing_id)
        )
        assert result.scalar_one_or_none() is None

    async def test_briefing_relationship(self, test_db):
        """Test relationship between Briefing and User."""
        from app.models.briefing import Briefing
        from datetime import date

        user = User(
            email="relation_briefing@example.com",
            password_hash="hashed",
            display_name="Relation Briefing User",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        briefing = Briefing(
            user_id=user.id,
            briefing_date=date.today(),
            content="Test briefing for relationship",
            tasks_suggested=[],
            wellbeing_snapshot={},
        )
        test_db.add(briefing)
        await test_db.commit()
        await test_db.refresh(briefing)

        # Load relationship
        result = await test_db.execute(
            select(Briefing).where(Briefing.id == briefing.id)
        )
        loaded_briefing = result.scalar_one()
        assert loaded_briefing.user.id == user.id
        assert loaded_briefing.user.email == "relation_briefing@example.com"

    async def test_briefing_status_update(self, test_db):
        """Test updating briefing status."""
        from app.models.briefing import Briefing, BriefingStatus
        from datetime import date, datetime, timezone

        user = User(
            email="status_briefing@example.com",
            password_hash="hashed",
            display_name="Status Briefing User",
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)

        briefing = Briefing(
            user_id=user.id,
            briefing_date=date.today(),
            content="Test briefing for status update",
            tasks_suggested=[],
            wellbeing_snapshot={},
            status=BriefingStatus.GENERATED,
        )
        test_db.add(briefing)
        await test_db.commit()
        await test_db.refresh(briefing)

        # Update status to READ with read_at timestamp
        briefing.status = BriefingStatus.READ
        briefing.read_at = datetime.now(timezone.utc)
        await test_db.commit()
        await test_db.refresh(briefing)

        assert briefing.status == BriefingStatus.READ
        assert briefing.read_at is not None
