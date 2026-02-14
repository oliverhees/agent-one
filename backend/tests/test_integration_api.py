"""Tests for Phase 10 integration API endpoints."""
import pytest
from uuid import uuid4
from httpx import AsyncClient


class TestCalendarAPI:
    @pytest.mark.asyncio
    async def test_calendar_status_not_connected(self, authenticated_client: AsyncClient, test_user):
        response = await authenticated_client.get("/api/v1/calendar/status")
        assert response.status_code == 200
        data = response.json()
        assert data["connected"] is False

    @pytest.mark.asyncio
    async def test_calendar_events_empty(self, authenticated_client: AsyncClient, test_user):
        response = await authenticated_client.get("/api/v1/calendar/events")
        assert response.status_code == 200
        data = response.json()
        assert data["events"] == []

    @pytest.mark.asyncio
    async def test_calendar_unauthorized(self, client: AsyncClient):
        response = await client.get("/api/v1/calendar/status")
        assert response.status_code == 403


class TestReminderAPI:
    @pytest.mark.asyncio
    async def test_list_reminders_empty(self, authenticated_client: AsyncClient, test_user):
        response = await authenticated_client.get("/api/v1/reminders")
        assert response.status_code == 200
        data = response.json()
        assert data["reminders"] == []
        assert data["total"] == 0

    @pytest.mark.asyncio
    async def test_create_reminder(self, authenticated_client: AsyncClient, test_user):
        response = await authenticated_client.post(
            "/api/v1/reminders",
            json={"title": "Test Reminder", "remind_at": "2026-12-31T10:00:00Z"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Reminder"
        assert data["source"] == "manual"
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_delete_nonexistent_reminder(self, authenticated_client: AsyncClient, test_user):
        response = await authenticated_client.delete(f"/api/v1/reminders/{uuid4()}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_reminders_unauthorized(self, client: AsyncClient):
        response = await client.get("/api/v1/reminders")
        assert response.status_code == 403


class TestWebhookAPI:
    @pytest.mark.asyncio
    async def test_list_webhooks_empty(self, authenticated_client: AsyncClient, test_user):
        response = await authenticated_client.get("/api/v1/webhooks")
        assert response.status_code == 200
        data = response.json()
        assert data["webhooks"] == []

    @pytest.mark.asyncio
    async def test_create_webhook(self, authenticated_client: AsyncClient, test_user):
        response = await authenticated_client.post(
            "/api/v1/webhooks",
            json={"name": "Test", "url": "https://example.com/hook", "direction": "outgoing", "events": ["task_completed"]},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test"
        assert data["direction"] == "outgoing"

    @pytest.mark.asyncio
    async def test_webhooks_unauthorized(self, client: AsyncClient):
        response = await client.get("/api/v1/webhooks")
        assert response.status_code == 403


class TestN8nAPI:
    @pytest.mark.asyncio
    async def test_list_workflows_empty(self, authenticated_client: AsyncClient, test_user):
        response = await authenticated_client.get("/api/v1/n8n/workflows")
        assert response.status_code == 200
        data = response.json()
        assert data["workflows"] == []

    @pytest.mark.asyncio
    async def test_create_workflow(self, authenticated_client: AsyncClient, test_user):
        response = await authenticated_client.post(
            "/api/v1/n8n/workflows",
            json={"name": "CRM Lead", "webhook_url": "https://n8n.example.com/webhook/abc"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "CRM Lead"

    @pytest.mark.asyncio
    async def test_n8n_unauthorized(self, client: AsyncClient):
        response = await client.get("/api/v1/n8n/workflows")
        assert response.status_code == 403


class TestRouterRegistration:
    def test_calendar_router_registered(self):
        from app.api.v1.router import router
        paths = [r.path for r in router.routes]
        assert any("/calendar" in p for p in paths)

    def test_reminders_router_registered(self):
        from app.api.v1.router import router
        paths = [r.path for r in router.routes]
        assert any("/reminders" in p for p in paths)

    def test_webhooks_router_registered(self):
        from app.api.v1.router import router
        paths = [r.path for r in router.routes]
        assert any("/webhooks" in p for p in paths)

    def test_n8n_router_registered(self):
        from app.api.v1.router import router
        paths = [r.path for r in router.routes]
        assert any("/n8n" in p for p in paths)
