"""Dashboard endpoint tests."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


# ===========================================================================
# Dashboard Summary (GET /api/v1/dashboard/summary)
# ===========================================================================

class TestDashboardSummary:
    """Tests for GET /api/v1/dashboard/summary."""

    async def test_empty_dashboard(self, authenticated_client: AsyncClient, test_user):
        """New user should get an empty but valid dashboard."""
        response = await authenticated_client.get("/api/v1/dashboard/summary")

        assert response.status_code == 200
        data = response.json()

        assert data["today_tasks"] == []
        assert data["gamification"]["total_xp"] == 0
        assert data["gamification"]["level"] == 1
        assert data["gamification"]["streak"] == 0
        assert data["gamification"]["progress_percent"] == 0.0
        assert data["next_deadline"] is None
        assert data["active_nudges_count"] == 0
        assert isinstance(data["motivational_quote"], str)
        assert len(data["motivational_quote"]) > 0

    async def test_dashboard_with_tasks(self, authenticated_client: AsyncClient, test_user):
        """Dashboard should show open tasks."""
        await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Task A", "priority": "high"},
        )
        await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Task B", "priority": "low"},
        )

        response = await authenticated_client.get("/api/v1/dashboard/summary")

        assert response.status_code == 200
        data = response.json()

        assert len(data["today_tasks"]) == 2

    async def test_dashboard_shows_next_deadline(
        self, authenticated_client: AsyncClient, test_user
    ):
        """Dashboard should show the next upcoming deadline."""
        future = (datetime.now(timezone.utc) + timedelta(hours=5)).isoformat()
        await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Deadline Task", "due_date": future},
        )

        response = await authenticated_client.get("/api/v1/dashboard/summary")

        assert response.status_code == 200
        data = response.json()

        assert data["next_deadline"] is not None
        assert data["next_deadline"]["task_title"] == "Deadline Task"

    async def test_dashboard_gamification_after_complete(
        self, authenticated_client: AsyncClient, test_user
    ):
        """Dashboard gamification should update after completing a task."""
        r = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Complete Me"},
        )
        task_id = r.json()["id"]
        await authenticated_client.post(f"/api/v1/tasks/{task_id}/complete")

        response = await authenticated_client.get("/api/v1/dashboard/summary")

        assert response.status_code == 200
        data = response.json()

        assert data["gamification"]["total_xp"] > 0
        assert data["gamification"]["streak"] >= 1

    async def test_dashboard_motivational_quote(
        self, authenticated_client: AsyncClient, test_user
    ):
        """Dashboard should always include a motivational quote."""
        response = await authenticated_client.get("/api/v1/dashboard/summary")

        assert response.status_code == 200
        data = response.json()

        assert "motivational_quote" in data
        assert isinstance(data["motivational_quote"], str)

    async def test_dashboard_unauthorized(self, client: AsyncClient):
        """403 without auth."""
        response = await client.get("/api/v1/dashboard/summary")
        assert response.status_code == 403

    async def test_dashboard_structure(self, authenticated_client: AsyncClient, test_user):
        """Dashboard response should have the correct top-level structure."""
        response = await authenticated_client.get("/api/v1/dashboard/summary")

        assert response.status_code == 200
        data = response.json()

        assert "today_tasks" in data
        assert "gamification" in data
        assert "next_deadline" in data
        assert "active_nudges_count" in data
        assert "motivational_quote" in data

        gamification = data["gamification"]
        assert "total_xp" in gamification
        assert "level" in gamification
        assert "streak" in gamification
        assert "progress_percent" in gamification
