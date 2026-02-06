"""Brain (Second Brain) endpoint tests."""

from uuid import uuid4

import pytest
from httpx import AsyncClient


class TestCreateBrainEntry:
    """Tests for POST /api/v1/brain/entries endpoint."""

    async def test_create_brain_entry(self, authenticated_client: AsyncClient, test_user):
        """Test creating a brain entry with all fields."""
        response = await authenticated_client.post(
            "/api/v1/brain/entries",
            json={
                "title": "Meeting-Notizen",
                "content": "Heute im Meeting wurde besprochen, dass das Projekt bis Freitag fertig sein muss.",
                "entry_type": "manual",
                "tags": ["meeting", "arbeit"],
                "source_url": "https://example.com/notes",
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert data["title"] == "Meeting-Notizen"
        assert data["content"] == "Heute im Meeting wurde besprochen, dass das Projekt bis Freitag fertig sein muss."
        assert data["entry_type"] == "manual"
        assert data["tags"] == ["meeting", "arbeit"]
        assert data["source_url"] == "https://example.com/notes"
        assert data["embedding_status"] == "pending"
        assert "id" in data
        assert "user_id" in data
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_brain_entry_minimal(self, authenticated_client: AsyncClient, test_user):
        """Test creating a brain entry with only required fields."""
        response = await authenticated_client.post(
            "/api/v1/brain/entries",
            json={
                "title": "Kurze Notiz",
                "content": "Das muss ich mir merken.",
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert data["title"] == "Kurze Notiz"
        assert data["entry_type"] == "manual"
        assert data["tags"] == []

    async def test_create_brain_entry_with_tags(self, authenticated_client: AsyncClient, test_user):
        """Test creating a brain entry with tags."""
        response = await authenticated_client.post(
            "/api/v1/brain/entries",
            json={
                "title": "Tagged Entry",
                "content": "Inhalt mit Tags.",
                "tags": ["python", "coding", "lernen"],
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["tags"] == ["python", "coding", "lernen"]

    async def test_create_brain_entry_validation_no_title(self, authenticated_client: AsyncClient, test_user):
        """Test that missing title is rejected."""
        response = await authenticated_client.post(
            "/api/v1/brain/entries",
            json={"content": "Nur Inhalt"},
        )
        assert response.status_code == 422

    async def test_create_brain_entry_validation_no_content(self, authenticated_client: AsyncClient, test_user):
        """Test that missing content is rejected."""
        response = await authenticated_client.post(
            "/api/v1/brain/entries",
            json={"title": "Nur Titel"},
        )
        assert response.status_code == 422

    async def test_create_brain_entry_validation_empty_title(self, authenticated_client: AsyncClient, test_user):
        """Test that empty title is rejected."""
        response = await authenticated_client.post(
            "/api/v1/brain/entries",
            json={"title": "", "content": "Inhalt"},
        )
        assert response.status_code == 422


class TestListBrainEntries:
    """Tests for GET /api/v1/brain/entries endpoint."""

    async def test_list_brain_entries_empty(self, authenticated_client: AsyncClient, test_user):
        """Test listing brain entries when none exist."""
        response = await authenticated_client.get("/api/v1/brain/entries")

        assert response.status_code == 200
        data = response.json()

        assert data["items"] == []
        assert data["total_count"] == 0

    async def test_list_brain_entries(self, authenticated_client: AsyncClient, test_user):
        """Test listing brain entries with data."""
        for i in range(3):
            await authenticated_client.post(
                "/api/v1/brain/entries",
                json={"title": f"Entry {i+1}", "content": f"Inhalt {i+1}"},
            )

        response = await authenticated_client.get("/api/v1/brain/entries")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total_count"] == 3

    async def test_list_brain_entries_filter_type(self, authenticated_client: AsyncClient, test_user):
        """Test filtering brain entries by type."""
        await authenticated_client.post(
            "/api/v1/brain/entries",
            json={"title": "Manual", "content": "Manueller Eintrag", "entry_type": "manual"},
        )
        await authenticated_client.post(
            "/api/v1/brain/entries",
            json={"title": "Voice", "content": "Sprach-Eintrag", "entry_type": "voice_note"},
        )

        response = await authenticated_client.get("/api/v1/brain/entries?entry_type=manual")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["entry_type"] == "manual"

    async def test_list_brain_entries_pagination(self, authenticated_client: AsyncClient, test_user):
        """Test brain entry pagination."""
        for i in range(5):
            await authenticated_client.post(
                "/api/v1/brain/entries",
                json={"title": f"Entry {i+1}", "content": f"Inhalt {i+1}"},
            )

        response = await authenticated_client.get("/api/v1/brain/entries?limit=2")
        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 2
        assert data["has_more"] is True
        assert data["total_count"] == 5


class TestGetBrainEntry:
    """Tests for GET /api/v1/brain/entries/{entry_id} endpoint."""

    async def test_get_brain_entry(self, authenticated_client: AsyncClient, test_user):
        """Test getting a specific brain entry."""
        create_resp = await authenticated_client.post(
            "/api/v1/brain/entries",
            json={"title": "Detail Entry", "content": "Detaillierter Inhalt"},
        )
        entry_id = create_resp.json()["id"]

        response = await authenticated_client.get(f"/api/v1/brain/entries/{entry_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == entry_id
        assert data["title"] == "Detail Entry"

    async def test_get_brain_entry_not_found(self, authenticated_client: AsyncClient, test_user):
        """Test getting a nonexistent brain entry."""
        fake_id = str(uuid4())
        response = await authenticated_client.get(f"/api/v1/brain/entries/{fake_id}")
        assert response.status_code == 404

    async def test_get_brain_entry_other_user(
        self, authenticated_client: AsyncClient, test_user, client: AsyncClient, second_user
    ):
        """Test that user B cannot see user A's brain entry."""
        create_resp = await authenticated_client.post(
            "/api/v1/brain/entries",
            json={"title": "Private", "content": "Geheime Notiz"},
        )
        entry_id = create_resp.json()["id"]

        _, second_token, _ = second_user
        response = await client.get(
            f"/api/v1/brain/entries/{entry_id}",
            headers={"Authorization": f"Bearer {second_token}"},
        )
        assert response.status_code == 404


class TestUpdateBrainEntry:
    """Tests for PUT /api/v1/brain/entries/{entry_id} endpoint."""

    async def test_update_brain_entry(self, authenticated_client: AsyncClient, test_user):
        """Test updating a brain entry."""
        create_resp = await authenticated_client.post(
            "/api/v1/brain/entries",
            json={"title": "Original", "content": "Alter Inhalt"},
        )
        entry_id = create_resp.json()["id"]

        response = await authenticated_client.put(
            f"/api/v1/brain/entries/{entry_id}",
            json={"title": "Aktualisiert", "content": "Neuer Inhalt"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Aktualisiert"
        assert data["content"] == "Neuer Inhalt"

    async def test_update_brain_entry_tags(self, authenticated_client: AsyncClient, test_user):
        """Test updating brain entry tags."""
        create_resp = await authenticated_client.post(
            "/api/v1/brain/entries",
            json={"title": "Tagtest", "content": "Inhalt", "tags": ["alt"]},
        )
        entry_id = create_resp.json()["id"]

        response = await authenticated_client.put(
            f"/api/v1/brain/entries/{entry_id}",
            json={"tags": ["neu1", "neu2"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == ["neu1", "neu2"]


class TestDeleteBrainEntry:
    """Tests for DELETE /api/v1/brain/entries/{entry_id} endpoint."""

    async def test_delete_brain_entry(self, authenticated_client: AsyncClient, test_user):
        """Test deleting a brain entry."""
        create_resp = await authenticated_client.post(
            "/api/v1/brain/entries",
            json={"title": "Zu loeschen", "content": "Wird geloescht"},
        )
        entry_id = create_resp.json()["id"]

        response = await authenticated_client.delete(f"/api/v1/brain/entries/{entry_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = await authenticated_client.get(f"/api/v1/brain/entries/{entry_id}")
        assert get_response.status_code == 404

    async def test_delete_brain_entry_not_found(self, authenticated_client: AsyncClient, test_user):
        """Test deleting a nonexistent brain entry."""
        fake_id = str(uuid4())
        response = await authenticated_client.delete(f"/api/v1/brain/entries/{fake_id}")
        assert response.status_code == 404


class TestSearchBrain:
    """Tests for GET /api/v1/brain/search endpoint."""

    async def test_search_brain(self, authenticated_client: AsyncClient, test_user):
        """Test searching brain entries."""
        await authenticated_client.post(
            "/api/v1/brain/entries",
            json={"title": "Python Tutorial", "content": "Python ist eine Programmiersprache."},
        )
        await authenticated_client.post(
            "/api/v1/brain/entries",
            json={"title": "Kochrezept", "content": "Reis kochen in 20 Minuten."},
        )

        response = await authenticated_client.get("/api/v1/brain/search?q=Python")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        assert data[0]["entry"]["title"] == "Python Tutorial"
        assert data[0]["score"] > 0

    async def test_search_brain_no_results(self, authenticated_client: AsyncClient, test_user):
        """Test search with no matching results."""
        await authenticated_client.post(
            "/api/v1/brain/entries",
            json={"title": "Etwas anderes", "content": "Kein Treffer hier."},
        )

        response = await authenticated_client.get("/api/v1/brain/search?q=xyznonexistent")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_search_brain_content_match(self, authenticated_client: AsyncClient, test_user):
        """Test that search also matches content, not just title."""
        await authenticated_client.post(
            "/api/v1/brain/entries",
            json={"title": "Notiz", "content": "Heute habe ich FastAPI gelernt und es war toll."},
        )

        response = await authenticated_client.get("/api/v1/brain/search?q=FastAPI")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1


class TestBrainAuth:
    """Tests for brain endpoints without authentication."""

    async def test_brain_unauthorized_list(self, client: AsyncClient):
        """Test listing brain entries without token returns 403."""
        response = await client.get("/api/v1/brain/entries")
        assert response.status_code == 403

    async def test_brain_unauthorized_create(self, client: AsyncClient):
        """Test creating a brain entry without token returns 403."""
        response = await client.post(
            "/api/v1/brain/entries",
            json={"title": "No auth", "content": "Test"},
        )
        assert response.status_code == 403

    async def test_brain_unauthorized_search(self, client: AsyncClient):
        """Test searching without token returns 403."""
        response = await client.get("/api/v1/brain/search?q=test")
        assert response.status_code == 403
