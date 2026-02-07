"""Task breakdown endpoint tests."""

import json
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4

import pytest
from httpx import AsyncClient


# ---------------------------------------------------------------------------
# Mock AI helper
# ---------------------------------------------------------------------------

def _mock_ai_stream(subtasks: list[dict]):
    """Create an AsyncMock that yields JSON subtask suggestions."""
    async def _stream(*args, **kwargs):
        payload = json.dumps(subtasks)
        yield payload
    return _stream


MOCK_SUBTASKS = [
    {"title": "Schritt 1", "description": "Ersten Schritt machen", "estimated_minutes": 10},
    {"title": "Schritt 2", "description": "Zweiten Schritt machen", "estimated_minutes": 15},
    {"title": "Schritt 3", "description": "Dritten Schritt machen", "estimated_minutes": 20},
]


# ===========================================================================
# Generate Breakdown (POST /api/v1/tasks/{id}/breakdown)
# ===========================================================================

class TestGenerateBreakdown:
    """Tests for POST /api/v1/tasks/{id}/breakdown."""

    @patch("app.services.task_breakdown.AIService")
    async def test_generate_breakdown(
        self, MockAI, authenticated_client: AsyncClient, test_user
    ):
        """Generate breakdown should return suggested subtasks."""
        mock_instance = MockAI.return_value
        mock_instance.stream_response = _mock_ai_stream(MOCK_SUBTASKS)

        # Create parent task
        r = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Grosser Task", "priority": "high", "estimated_minutes": 120},
        )
        task_id = r.json()["id"]

        response = await authenticated_client.post(f"/api/v1/tasks/{task_id}/breakdown")

        assert response.status_code == 200
        data = response.json()

        assert data["parent_task"]["id"] == task_id
        assert data["parent_task"]["title"] == "Grosser Task"
        assert len(data["suggested_subtasks"]) == 3
        assert data["suggested_subtasks"][0]["order"] == 1
        assert data["suggested_subtasks"][0]["title"] == "Schritt 1"

    async def test_breakdown_task_not_found(self, authenticated_client: AsyncClient, test_user):
        """404 when task does not exist."""
        fake_id = str(uuid4())
        response = await authenticated_client.post(f"/api/v1/tasks/{fake_id}/breakdown")
        assert response.status_code == 404

    @patch("app.services.task_breakdown.AIService")
    async def test_breakdown_already_has_subtasks(
        self, MockAI, authenticated_client: AsyncClient, test_user
    ):
        """409 when task already has subtasks."""
        mock_instance = MockAI.return_value
        mock_instance.stream_response = _mock_ai_stream(MOCK_SUBTASKS)

        r = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Parent Task"},
        )
        parent_id = r.json()["id"]

        # Create a child task manually to simulate existing subtasks
        await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Child Task", "parent_id": parent_id},
        )

        response = await authenticated_client.post(f"/api/v1/tasks/{parent_id}/breakdown")
        assert response.status_code == 409

    async def test_breakdown_unauthorized(self, client: AsyncClient):
        """401/403 without auth."""
        fake_id = str(uuid4())
        response = await client.post(f"/api/v1/tasks/{fake_id}/breakdown")
        assert response.status_code == 403


# ===========================================================================
# Confirm Breakdown (POST /api/v1/tasks/{id}/breakdown/confirm)
# ===========================================================================

class TestConfirmBreakdown:
    """Tests for POST /api/v1/tasks/{id}/breakdown/confirm."""

    async def test_confirm_creates_subtasks(self, authenticated_client: AsyncClient, test_user):
        """Confirm should create subtasks under the parent."""
        r = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Parent Task", "priority": "high", "tags": ["arbeit"]},
        )
        parent_id = r.json()["id"]

        subtasks = [
            {"title": "Sub 1", "description": "First step", "estimated_minutes": 10},
            {"title": "Sub 2", "description": "Second step", "estimated_minutes": 20},
        ]

        response = await authenticated_client.post(
            f"/api/v1/tasks/{parent_id}/breakdown/confirm",
            json={"subtasks": subtasks},
        )

        assert response.status_code == 201
        data = response.json()

        assert data["parent_task"]["id"] == parent_id
        assert data["parent_task"]["status"] == "in_progress"
        assert len(data["created_subtasks"]) == 2

    async def test_confirm_subtasks_inherit_parent_priority(
        self, authenticated_client: AsyncClient, test_user
    ):
        """Sub-tasks should inherit priority from parent."""
        r = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Urgent Parent", "priority": "urgent"},
        )
        parent_id = r.json()["id"]

        response = await authenticated_client.post(
            f"/api/v1/tasks/{parent_id}/breakdown/confirm",
            json={"subtasks": [{"title": "Sub A"}]},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["created_subtasks"][0]["priority"] == "urgent"

    async def test_confirm_subtasks_have_parent_id(
        self, authenticated_client: AsyncClient, test_user
    ):
        """Sub-tasks should have parent_id set."""
        r = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Parent"},
        )
        parent_id = r.json()["id"]

        response = await authenticated_client.post(
            f"/api/v1/tasks/{parent_id}/breakdown/confirm",
            json={"subtasks": [{"title": "Sub"}]},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["created_subtasks"][0]["parent_id"] == parent_id

    async def test_confirm_subtasks_have_breakdown_source(
        self, authenticated_client: AsyncClient, test_user
    ):
        """Sub-tasks should have source='breakdown'."""
        r = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Parent"},
        )
        parent_id = r.json()["id"]

        response = await authenticated_client.post(
            f"/api/v1/tasks/{parent_id}/breakdown/confirm",
            json={"subtasks": [{"title": "Sub"}]},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["created_subtasks"][0]["source"] == "breakdown"

    async def test_confirm_subtasks_inherit_tags(
        self, authenticated_client: AsyncClient, test_user
    ):
        """Sub-tasks should inherit tags from parent."""
        r = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Tagged Parent", "tags": ["arbeit", "wichtig"]},
        )
        parent_id = r.json()["id"]

        response = await authenticated_client.post(
            f"/api/v1/tasks/{parent_id}/breakdown/confirm",
            json={"subtasks": [{"title": "Sub"}]},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["created_subtasks"][0]["tags"] == ["arbeit", "wichtig"]

    async def test_confirm_task_not_found(self, authenticated_client: AsyncClient, test_user):
        """404 when parent task does not exist."""
        fake_id = str(uuid4())
        response = await authenticated_client.post(
            f"/api/v1/tasks/{fake_id}/breakdown/confirm",
            json={"subtasks": [{"title": "Sub"}]},
        )
        assert response.status_code == 404

    async def test_confirm_unauthorized(self, client: AsyncClient):
        """403 without auth."""
        fake_id = str(uuid4())
        response = await client.post(
            f"/api/v1/tasks/{fake_id}/breakdown/confirm",
            json={"subtasks": [{"title": "Sub"}]},
        )
        assert response.status_code == 403
