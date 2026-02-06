"""Task endpoint tests."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient


class TestCreateTask:
    """Tests for POST /api/v1/tasks endpoint."""

    async def test_create_task(self, authenticated_client: AsyncClient, test_user):
        """Test creating a task with all fields."""
        response = await authenticated_client.post(
            "/api/v1/tasks/",
            json={
                "title": "Arzttermin vereinbaren",
                "description": "Termin beim Hausarzt machen",
                "priority": "high",
                "tags": ["gesundheit", "wichtig"],
                "estimated_minutes": 30,
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert data["title"] == "Arzttermin vereinbaren"
        assert data["description"] == "Termin beim Hausarzt machen"
        assert data["priority"] == "high"
        assert data["status"] == "open"
        assert data["tags"] == ["gesundheit", "wichtig"]
        assert data["estimated_minutes"] == 30
        assert data["xp_earned"] == 0
        assert data["is_recurring"] is False
        assert data["source"] == "manual"
        assert "id" in data
        assert "user_id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_task_minimal(self, authenticated_client: AsyncClient, test_user):
        """Test creating a task with only the required title field."""
        response = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Einfacher Task"},
        )

        assert response.status_code == 201
        data = response.json()

        assert data["title"] == "Einfacher Task"
        assert data["priority"] == "medium"
        assert data["status"] == "open"
        assert data["description"] is None
        assert data["tags"] == []

    async def test_create_task_with_due_date(self, authenticated_client: AsyncClient, test_user):
        """Test creating a task with a due date."""
        due = (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()
        response = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Fristaufgabe", "due_date": due},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["due_date"] is not None

    async def test_create_task_validation_empty_title(self, authenticated_client: AsyncClient, test_user):
        """Test that empty title is rejected."""
        response = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": ""},
        )
        assert response.status_code == 422

    async def test_create_task_validation_missing_title(self, authenticated_client: AsyncClient, test_user):
        """Test that missing title is rejected."""
        response = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"description": "Nur Beschreibung"},
        )
        assert response.status_code == 422


class TestListTasks:
    """Tests for GET /api/v1/tasks endpoint."""

    async def test_list_tasks_empty(self, authenticated_client: AsyncClient, test_user):
        """Test listing tasks when none exist."""
        response = await authenticated_client.get("/api/v1/tasks/")

        assert response.status_code == 200
        data = response.json()

        assert data["items"] == []
        assert data["total_count"] == 0
        assert data["has_more"] is False
        assert data["next_cursor"] is None

    async def test_list_tasks(self, authenticated_client: AsyncClient, test_user):
        """Test listing tasks with data."""
        # Create 3 tasks
        for i in range(3):
            await authenticated_client.post(
                "/api/v1/tasks/",
                json={"title": f"Task {i+1}"},
            )

        response = await authenticated_client.get("/api/v1/tasks/")

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 3
        assert data["total_count"] == 3

    async def test_list_tasks_filter_status(self, authenticated_client: AsyncClient, test_user):
        """Test filtering tasks by status."""
        # Create tasks
        r1 = await authenticated_client.post("/api/v1/tasks/", json={"title": "Open Task"})
        r2 = await authenticated_client.post("/api/v1/tasks/", json={"title": "Done Task"})

        # Complete one task
        task_id = r2.json()["id"]
        await authenticated_client.post(f"/api/v1/tasks/{task_id}/complete")

        response = await authenticated_client.get("/api/v1/tasks/?status=open")

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Open Task"

    async def test_list_tasks_filter_priority(self, authenticated_client: AsyncClient, test_user):
        """Test filtering tasks by priority."""
        await authenticated_client.post("/api/v1/tasks/", json={"title": "Low", "priority": "low"})
        await authenticated_client.post("/api/v1/tasks/", json={"title": "High", "priority": "high"})

        response = await authenticated_client.get("/api/v1/tasks/?priority=high")

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 1
        assert data["items"][0]["priority"] == "high"

    async def test_list_tasks_pagination(self, authenticated_client: AsyncClient, test_user):
        """Test task pagination."""
        for i in range(5):
            await authenticated_client.post("/api/v1/tasks/", json={"title": f"Task {i+1}"})

        # Get first page with limit=2
        response = await authenticated_client.get("/api/v1/tasks/?limit=2")
        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 2
        assert data["has_more"] is True
        assert data["next_cursor"] is not None
        assert data["total_count"] == 5


class TestGetTask:
    """Tests for GET /api/v1/tasks/{task_id} endpoint."""

    async def test_get_task(self, authenticated_client: AsyncClient, test_user):
        """Test getting a specific task."""
        create_resp = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Detail Task", "priority": "urgent"},
        )
        task_id = create_resp.json()["id"]

        response = await authenticated_client.get(f"/api/v1/tasks/{task_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == task_id
        assert data["title"] == "Detail Task"
        assert data["priority"] == "urgent"

    async def test_get_task_not_found(self, authenticated_client: AsyncClient, test_user):
        """Test getting a nonexistent task."""
        fake_id = str(uuid4())
        response = await authenticated_client.get(f"/api/v1/tasks/{fake_id}")
        assert response.status_code == 404

    async def test_get_task_other_user(
        self, authenticated_client: AsyncClient, test_user, client: AsyncClient, second_user
    ):
        """Test that user B cannot see user A's task."""
        # Create task as user A
        create_resp = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Private Task"},
        )
        task_id = create_resp.json()["id"]

        # Try to access as user B
        _, second_token, _ = second_user
        response = await client.get(
            f"/api/v1/tasks/{task_id}",
            headers={"Authorization": f"Bearer {second_token}"},
        )
        assert response.status_code == 404


class TestUpdateTask:
    """Tests for PUT /api/v1/tasks/{task_id} endpoint."""

    async def test_update_task(self, authenticated_client: AsyncClient, test_user):
        """Test updating a task."""
        create_resp = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Original", "priority": "low"},
        )
        task_id = create_resp.json()["id"]

        response = await authenticated_client.put(
            f"/api/v1/tasks/{task_id}",
            json={"title": "Updated", "priority": "high"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated"
        assert data["priority"] == "high"

    async def test_update_task_partial(self, authenticated_client: AsyncClient, test_user):
        """Test partial update of a task (only title)."""
        create_resp = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Original", "priority": "low"},
        )
        task_id = create_resp.json()["id"]

        response = await authenticated_client.put(
            f"/api/v1/tasks/{task_id}",
            json={"title": "Nur Title geaendert"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Nur Title geaendert"
        assert data["priority"] == "low"  # unchanged


class TestDeleteTask:
    """Tests for DELETE /api/v1/tasks/{task_id} endpoint."""

    async def test_delete_task(self, authenticated_client: AsyncClient, test_user):
        """Test deleting a task."""
        create_resp = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Zu loeschen"},
        )
        task_id = create_resp.json()["id"]

        response = await authenticated_client.delete(f"/api/v1/tasks/{task_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = await authenticated_client.get(f"/api/v1/tasks/{task_id}")
        assert get_response.status_code == 404

    async def test_delete_task_not_found(self, authenticated_client: AsyncClient, test_user):
        """Test deleting a nonexistent task."""
        fake_id = str(uuid4())
        response = await authenticated_client.delete(f"/api/v1/tasks/{fake_id}")
        assert response.status_code == 404


class TestCompleteTask:
    """Tests for POST /api/v1/tasks/{task_id}/complete endpoint."""

    async def test_complete_task(self, authenticated_client: AsyncClient, test_user):
        """Test completing a task and earning XP."""
        create_resp = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Zu erledigen", "priority": "medium"},
        )
        task_id = create_resp.json()["id"]

        response = await authenticated_client.post(f"/api/v1/tasks/{task_id}/complete")

        assert response.status_code == 200
        data = response.json()

        assert data["xp_earned"] > 0
        assert data["new_total_xp"] >= data["xp_earned"]
        assert "level_up" in data
        assert data["task"]["status"] == "done"
        assert data["task"]["completed_at"] is not None

    async def test_complete_task_already_done(self, authenticated_client: AsyncClient, test_user):
        """Test completing a task that is already done returns 409."""
        create_resp = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Schon erledigt"},
        )
        task_id = create_resp.json()["id"]

        # Complete once
        await authenticated_client.post(f"/api/v1/tasks/{task_id}/complete")

        # Try again
        response = await authenticated_client.post(f"/api/v1/tasks/{task_id}/complete")
        assert response.status_code == 409

    async def test_complete_urgent_task_xp(self, authenticated_client: AsyncClient, test_user):
        """Test that urgent tasks give 100 base XP."""
        create_resp = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Dringend", "priority": "urgent"},
        )
        task_id = create_resp.json()["id"]

        response = await authenticated_client.post(f"/api/v1/tasks/{task_id}/complete")

        assert response.status_code == 200
        data = response.json()
        # Urgent base XP = 100 (no due date, so no on-time bonus)
        assert data["xp_earned"] == 100

    async def test_complete_low_priority_task_xp(self, authenticated_client: AsyncClient, test_user):
        """Test that low priority tasks give 10 base XP."""
        create_resp = await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Unwichtig", "priority": "low"},
        )
        task_id = create_resp.json()["id"]

        response = await authenticated_client.post(f"/api/v1/tasks/{task_id}/complete")

        assert response.status_code == 200
        data = response.json()
        assert data["xp_earned"] == 10


class TestTodayTasks:
    """Tests for GET /api/v1/tasks/today endpoint."""

    async def test_today_tasks_empty(self, authenticated_client: AsyncClient, test_user):
        """Test getting today's tasks when none exist."""
        response = await authenticated_client.get("/api/v1/tasks/today")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_today_tasks_with_due_today(self, authenticated_client: AsyncClient, test_user):
        """Test getting tasks due today."""
        # Create a task due today
        now = datetime.now(timezone.utc)
        due_today = now.replace(hour=23, minute=0, second=0).isoformat()
        await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Heute faellig", "due_date": due_today},
        )

        # Create a task due tomorrow (should NOT appear)
        due_tomorrow = (now + timedelta(days=1)).isoformat()
        await authenticated_client.post(
            "/api/v1/tasks/",
            json={"title": "Morgen faellig", "due_date": due_tomorrow},
        )

        response = await authenticated_client.get("/api/v1/tasks/today")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Heute faellig"


class TestTaskAuth:
    """Tests for task endpoints without authentication."""

    async def test_tasks_unauthorized_list(self, client: AsyncClient):
        """Test listing tasks without token returns 403."""
        response = await client.get("/api/v1/tasks/")
        assert response.status_code == 403

    async def test_tasks_unauthorized_create(self, client: AsyncClient):
        """Test creating a task without token returns 403."""
        response = await client.post("/api/v1/tasks/", json={"title": "No auth"})
        assert response.status_code == 403

    async def test_tasks_unauthorized_today(self, client: AsyncClient):
        """Test today endpoint without token returns 403."""
        response = await client.get("/api/v1/tasks/today")
        assert response.status_code == 403
