"""Proactive mentioned items endpoint tests."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient


class TestListMentionedItems:
    """Tests for GET /api/v1/proactive/mentioned-items endpoint."""

    async def test_list_mentioned_items_empty(self, authenticated_client: AsyncClient, test_user):
        """Test listing mentioned items when none exist."""
        response = await authenticated_client.get("/api/v1/proactive/mentioned-items")

        assert response.status_code == 200
        data = response.json()

        assert data["items"] == []
        assert data["total_count"] == 0
        assert data["has_more"] is False
        assert data["next_cursor"] is None


class TestConvertMentionedItem:
    """Tests for POST /api/v1/proactive/mentioned-items/{item_id}/convert endpoint."""

    async def test_convert_item_not_found(self, authenticated_client: AsyncClient, test_user):
        """Test converting a nonexistent mentioned item returns 404."""
        fake_id = str(uuid4())
        response = await authenticated_client.post(
            f"/api/v1/proactive/mentioned-items/{fake_id}/convert",
            json={"convert_to": "task"},
        )
        assert response.status_code == 404


class TestDismissMentionedItem:
    """Tests for POST /api/v1/proactive/mentioned-items/{item_id}/dismiss endpoint."""

    async def test_dismiss_item_not_found(self, authenticated_client: AsyncClient, test_user):
        """Test dismissing a nonexistent mentioned item returns 404."""
        fake_id = str(uuid4())
        response = await authenticated_client.post(
            f"/api/v1/proactive/mentioned-items/{fake_id}/dismiss",
        )
        assert response.status_code == 404


class TestSnoozeMentionedItem:
    """Tests for POST /api/v1/proactive/mentioned-items/{item_id}/snooze endpoint."""

    async def test_snooze_item_not_found(self, authenticated_client: AsyncClient, test_user):
        """Test snoozing a nonexistent mentioned item returns 404."""
        fake_id = str(uuid4())
        snooze_until = (datetime.now(timezone.utc) + timedelta(hours=2)).isoformat()
        response = await authenticated_client.post(
            f"/api/v1/proactive/mentioned-items/{fake_id}/snooze",
            json={"until": snooze_until},
        )
        assert response.status_code == 404


class TestProactiveAuth:
    """Tests for proactive endpoints without authentication."""

    async def test_proactive_unauthorized_list(self, client: AsyncClient):
        """Test listing mentioned items without token returns 403."""
        response = await client.get("/api/v1/proactive/mentioned-items")
        assert response.status_code == 403

    async def test_proactive_unauthorized_convert(self, client: AsyncClient):
        """Test converting without token returns 403."""
        fake_id = str(uuid4())
        response = await client.post(
            f"/api/v1/proactive/mentioned-items/{fake_id}/convert",
            json={"convert_to": "task"},
        )
        assert response.status_code == 403

    async def test_proactive_unauthorized_dismiss(self, client: AsyncClient):
        """Test dismissing without token returns 403."""
        fake_id = str(uuid4())
        response = await client.post(
            f"/api/v1/proactive/mentioned-items/{fake_id}/dismiss",
        )
        assert response.status_code == 403

    async def test_proactive_unauthorized_snooze(self, client: AsyncClient):
        """Test snoozing without token returns 403."""
        fake_id = str(uuid4())
        snooze_until = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
        response = await client.post(
            f"/api/v1/proactive/mentioned-items/{fake_id}/snooze",
            json={"until": snooze_until},
        )
        assert response.status_code == 403
