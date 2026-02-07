"""Nudge endpoint tests."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.models.nudge_history import NudgeHistory, NudgeType
from app.services.nudge import NudgeService


TEST_DATABASE_URL = "postgresql+asyncpg://alice:alice_dev_123@localhost:5432/alice_test"


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

async def _create_task(client: AsyncClient, title: str = "Test Task") -> str:
    """Create a task and return its id."""
    r = await client.post("/api/v1/tasks/", json={"title": title})
    assert r.status_code == 201
    return r.json()["id"]


async def _create_nudge_direct(
    user_id: str,
    task_id: str | None = None,
    level: int = 1,
    nudge_type: NudgeType = NudgeType.FOLLOW_UP,
    message: str = "Hey, magst du den Task angehen?",
) -> str:
    """Create a nudge using a short-lived connection. Returns nudge id."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        service = NudgeService(session)
        nudge = await service.create_nudge(
            user_id=user_id,
            task_id=task_id,
            level=level,
            nudge_type=nudge_type,
            message=message,
        )
        await session.commit()
        nudge_id = str(nudge.id)
    await engine.dispose()
    return nudge_id


# ===========================================================================
# List Active Nudges (GET /api/v1/nudges)
# ===========================================================================

class TestListNudges:
    """Tests for GET /api/v1/nudges."""

    async def test_list_empty(self, authenticated_client: AsyncClient, test_user):
        """New user should have no active nudges."""
        response = await authenticated_client.get("/api/v1/nudges")

        assert response.status_code == 200
        data = response.json()

        assert data["nudges"] == []
        assert data["count"] == 0

    async def test_list_with_nudges(self, authenticated_client: AsyncClient, test_user):
        """Should list unacknowledged nudges."""
        user_data, _, _ = test_user

        task_id = await _create_task(authenticated_client)
        await _create_nudge_direct(user_data["id"], task_id)

        response = await authenticated_client.get("/api/v1/nudges")

        assert response.status_code == 200
        data = response.json()

        assert data["count"] == 1
        assert len(data["nudges"]) == 1
        nudge = data["nudges"][0]
        assert nudge["task_id"] == task_id
        assert nudge["nudge_level"] == "gentle"
        assert nudge["nudge_type"] == "follow_up"
        assert nudge["message"] == "Hey, magst du den Task angehen?"

    async def test_list_unauthorized(self, client: AsyncClient):
        """403 without auth."""
        response = await client.get("/api/v1/nudges")
        assert response.status_code == 403


# ===========================================================================
# Acknowledge Nudge (POST /api/v1/nudges/{id}/acknowledge)
# ===========================================================================

class TestAcknowledgeNudge:
    """Tests for POST /api/v1/nudges/{id}/acknowledge."""

    async def test_acknowledge_nudge(self, authenticated_client: AsyncClient, test_user):
        """Acknowledging a nudge should return acknowledged_at."""
        user_data, _, _ = test_user

        task_id = await _create_task(authenticated_client)
        nudge_id = await _create_nudge_direct(user_data["id"], task_id)

        response = await authenticated_client.post(
            f"/api/v1/nudges/{nudge_id}/acknowledge"
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == nudge_id
        assert data["acknowledged_at"] is not None

    async def test_acknowledge_removes_from_active(
        self, authenticated_client: AsyncClient, test_user
    ):
        """Acknowledged nudge should no longer appear in active list."""
        user_data, _, _ = test_user

        task_id = await _create_task(authenticated_client)
        nudge_id = await _create_nudge_direct(user_data["id"], task_id)

        await authenticated_client.post(f"/api/v1/nudges/{nudge_id}/acknowledge")

        response = await authenticated_client.get("/api/v1/nudges")
        data = response.json()
        assert data["count"] == 0

    async def test_acknowledge_already_acknowledged(
        self, authenticated_client: AsyncClient, test_user
    ):
        """Acknowledging twice should return 409."""
        user_data, _, _ = test_user

        task_id = await _create_task(authenticated_client)
        nudge_id = await _create_nudge_direct(user_data["id"], task_id)

        await authenticated_client.post(f"/api/v1/nudges/{nudge_id}/acknowledge")
        response = await authenticated_client.post(f"/api/v1/nudges/{nudge_id}/acknowledge")

        assert response.status_code == 409

    async def test_acknowledge_not_found(self, authenticated_client: AsyncClient, test_user):
        """404 for non-existent nudge."""
        fake_id = str(uuid4())
        response = await authenticated_client.post(f"/api/v1/nudges/{fake_id}/acknowledge")
        assert response.status_code == 404

    async def test_acknowledge_unauthorized(self, client: AsyncClient):
        """403 without auth."""
        fake_id = str(uuid4())
        response = await client.post(f"/api/v1/nudges/{fake_id}/acknowledge")
        assert response.status_code == 403


# ===========================================================================
# Nudge History (GET /api/v1/nudges/history)
# ===========================================================================

class TestNudgeHistory:
    """Tests for GET /api/v1/nudges/history."""

    async def test_history_empty(self, authenticated_client: AsyncClient, test_user):
        """Empty history for new user."""
        response = await authenticated_client.get("/api/v1/nudges/history")

        assert response.status_code == 200
        data = response.json()

        assert data["items"] == []
        assert data["total_count"] == 0
        assert data["has_more"] is False

    async def test_history_with_nudges(self, authenticated_client: AsyncClient, test_user):
        """History should include all nudges (acknowledged and not)."""
        user_data, _, _ = test_user

        task_id = await _create_task(authenticated_client)
        await _create_nudge_direct(user_data["id"], task_id, message="Nudge 1")
        await _create_nudge_direct(user_data["id"], task_id, message="Nudge 2")

        response = await authenticated_client.get("/api/v1/nudges/history")

        assert response.status_code == 200
        data = response.json()

        assert data["total_count"] == 2
        assert len(data["items"]) == 2

    async def test_history_unauthorized(self, client: AsyncClient):
        """403 without auth."""
        response = await client.get("/api/v1/nudges/history")
        assert response.status_code == 403


# ===========================================================================
# Nudge Types and Levels
# ===========================================================================

class TestNudgeTypesAndLevels:
    """Test different nudge types and levels."""

    async def test_nudge_levels(self, authenticated_client: AsyncClient, test_user):
        """Nudge levels 1/2/3 should map to gentle/moderate/firm."""
        user_data, _, _ = test_user
        task_id = await _create_task(authenticated_client)

        for level, expected_name in [(1, "gentle"), (2, "moderate"), (3, "firm")]:
            await _create_nudge_direct(
                user_data["id"], task_id,
                level=level, message=f"Level {level}"
            )

        response = await authenticated_client.get("/api/v1/nudges")
        data = response.json()

        levels_found = {n["nudge_level"] for n in data["nudges"]}
        assert levels_found == {"gentle", "moderate", "firm"}

    async def test_nudge_types(self, authenticated_client: AsyncClient, test_user):
        """Different NudgeType enums should map to API type strings."""
        user_data, _, _ = test_user
        task_id = await _create_task(authenticated_client)

        for nt in [NudgeType.FOLLOW_UP, NudgeType.DEADLINE]:
            await _create_nudge_direct(
                user_data["id"], task_id,
                nudge_type=nt, message=f"Type {nt.value}"
            )

        response = await authenticated_client.get("/api/v1/nudges")
        data = response.json()

        types_found = {n["nudge_type"] for n in data["nudges"]}
        assert "follow_up" in types_found
        assert "deadline_approaching" in types_found
