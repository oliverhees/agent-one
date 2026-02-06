"""Personality profile and template endpoint tests."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.personality_template import PersonalityTemplate


class TestCreatePersonalityProfile:
    """Tests for POST /api/v1/personality/profiles endpoint."""

    async def test_create_personality_profile(self, authenticated_client: AsyncClient, test_user):
        """Test creating a personality profile."""
        response = await authenticated_client.post(
            "/api/v1/personality/profiles",
            json={
                "name": "Mein Coach",
                "traits": {"formality": 70, "humor": 30, "strictness": 80, "empathy": 50, "verbosity": 40},
                "custom_instructions": "Sprich mich immer mit Du an",
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == "Mein Coach"
        assert data["traits"]["formality"] == 70
        assert data["traits"]["humor"] == 30
        assert data["traits"]["strictness"] == 80
        assert data["traits"]["empathy"] == 50
        assert data["traits"]["verbosity"] == 40
        assert data["custom_instructions"] == "Sprich mich immer mit Du an"
        assert data["is_active"] is False
        assert "id" in data
        assert "user_id" in data
        assert "created_at" in data

    async def test_create_profile_minimal(self, authenticated_client: AsyncClient, test_user):
        """Test creating a personality profile with only name."""
        response = await authenticated_client.post(
            "/api/v1/personality/profiles",
            json={"name": "Minimal Profile"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Profile"
        assert data["is_active"] is False

    async def test_create_profile_from_template(
        self, authenticated_client: AsyncClient, test_user, test_db: AsyncSession
    ):
        """Test creating a profile from a template (traits are copied)."""
        # Create a template directly in DB
        template = PersonalityTemplate(
            name="Test Template",
            description="A test template",
            traits={"formality": 90, "humor": 10, "strictness": 80, "empathy": 30, "verbosity": 20},
            rules=[{"text": "Sei immer professionell"}],
            is_default=False,
        )
        test_db.add(template)
        await test_db.commit()
        await test_db.refresh(template)

        response = await authenticated_client.post(
            "/api/v1/personality/profiles",
            json={
                "name": "Von Template",
                "template_id": str(template.id),
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Von Template"
        assert data["template_id"] == str(template.id)
        # Traits should be copied from template
        assert data["traits"]["formality"] == 90
        assert data["traits"]["strictness"] == 80

    async def test_create_profile_validation_no_name(self, authenticated_client: AsyncClient, test_user):
        """Test that missing name is rejected."""
        response = await authenticated_client.post(
            "/api/v1/personality/profiles",
            json={"traits": {"formality": 50}},
        )
        assert response.status_code == 422

    async def test_create_profile_validation_empty_name(self, authenticated_client: AsyncClient, test_user):
        """Test that empty name is rejected."""
        response = await authenticated_client.post(
            "/api/v1/personality/profiles",
            json={"name": ""},
        )
        assert response.status_code == 422


class TestListPersonalityProfiles:
    """Tests for GET /api/v1/personality/profiles endpoint."""

    async def test_list_profiles_empty(self, authenticated_client: AsyncClient, test_user):
        """Test listing profiles when none exist."""
        response = await authenticated_client.get("/api/v1/personality/profiles")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    async def test_list_profiles(self, authenticated_client: AsyncClient, test_user):
        """Test listing profiles with data."""
        for name in ["Profil A", "Profil B", "Profil C"]:
            await authenticated_client.post(
                "/api/v1/personality/profiles",
                json={"name": name},
            )

        response = await authenticated_client.get("/api/v1/personality/profiles")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3


class TestUpdatePersonalityProfile:
    """Tests for PUT /api/v1/personality/profiles/{profile_id} endpoint."""

    async def test_update_profile(self, authenticated_client: AsyncClient, test_user):
        """Test updating a personality profile."""
        create_resp = await authenticated_client.post(
            "/api/v1/personality/profiles",
            json={"name": "Original"},
        )
        profile_id = create_resp.json()["id"]

        response = await authenticated_client.put(
            f"/api/v1/personality/profiles/{profile_id}",
            json={
                "name": "Umbenannt",
                "traits": {"formality": 100, "humor": 0, "strictness": 100, "empathy": 10, "verbosity": 10},
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Umbenannt"
        assert data["traits"]["formality"] == 100

    async def test_update_profile_not_found(self, authenticated_client: AsyncClient, test_user):
        """Test updating a nonexistent profile."""
        fake_id = str(uuid4())
        response = await authenticated_client.put(
            f"/api/v1/personality/profiles/{fake_id}",
            json={"name": "Nope"},
        )
        assert response.status_code == 404


class TestDeletePersonalityProfile:
    """Tests for DELETE /api/v1/personality/profiles/{profile_id} endpoint."""

    async def test_delete_profile(self, authenticated_client: AsyncClient, test_user):
        """Test deleting an inactive personality profile."""
        create_resp = await authenticated_client.post(
            "/api/v1/personality/profiles",
            json={"name": "Zu loeschen"},
        )
        profile_id = create_resp.json()["id"]

        response = await authenticated_client.delete(f"/api/v1/personality/profiles/{profile_id}")
        assert response.status_code == 204

        # Verify it's gone
        list_resp = await authenticated_client.get("/api/v1/personality/profiles")
        assert len(list_resp.json()) == 0

    async def test_delete_active_profile(self, authenticated_client: AsyncClient, test_user):
        """Test that deleting an active profile returns 409."""
        create_resp = await authenticated_client.post(
            "/api/v1/personality/profiles",
            json={"name": "Aktives Profil"},
        )
        profile_id = create_resp.json()["id"]

        # Activate it
        await authenticated_client.post(f"/api/v1/personality/profiles/{profile_id}/activate")

        # Try to delete
        response = await authenticated_client.delete(f"/api/v1/personality/profiles/{profile_id}")
        assert response.status_code == 409

    async def test_delete_profile_not_found(self, authenticated_client: AsyncClient, test_user):
        """Test deleting a nonexistent profile."""
        fake_id = str(uuid4())
        response = await authenticated_client.delete(f"/api/v1/personality/profiles/{fake_id}")
        assert response.status_code == 404


class TestActivateProfile:
    """Tests for POST /api/v1/personality/profiles/{profile_id}/activate endpoint."""

    async def test_activate_profile(self, authenticated_client: AsyncClient, test_user):
        """Test activating a personality profile."""
        create_resp = await authenticated_client.post(
            "/api/v1/personality/profiles",
            json={"name": "Zu aktivieren"},
        )
        profile_id = create_resp.json()["id"]

        response = await authenticated_client.post(
            f"/api/v1/personality/profiles/{profile_id}/activate"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_active"] is True

    async def test_activate_deactivates_other(self, authenticated_client: AsyncClient, test_user):
        """Test that activating a profile deactivates the previously active one."""
        # Create and activate profile A
        resp_a = await authenticated_client.post(
            "/api/v1/personality/profiles",
            json={"name": "Profil A"},
        )
        id_a = resp_a.json()["id"]
        await authenticated_client.post(f"/api/v1/personality/profiles/{id_a}/activate")

        # Create and activate profile B
        resp_b = await authenticated_client.post(
            "/api/v1/personality/profiles",
            json={"name": "Profil B"},
        )
        id_b = resp_b.json()["id"]
        await authenticated_client.post(f"/api/v1/personality/profiles/{id_b}/activate")

        # Fetch all profiles
        list_resp = await authenticated_client.get("/api/v1/personality/profiles")
        profiles = list_resp.json()

        active_profiles = [p for p in profiles if p["is_active"]]
        assert len(active_profiles) == 1
        assert active_profiles[0]["id"] == id_b

    async def test_activate_nonexistent_profile(self, authenticated_client: AsyncClient, test_user):
        """Test activating a nonexistent profile."""
        fake_id = str(uuid4())
        response = await authenticated_client.post(
            f"/api/v1/personality/profiles/{fake_id}/activate"
        )
        assert response.status_code == 404


class TestListTemplates:
    """Tests for GET /api/v1/personality/templates endpoint."""

    async def test_list_templates(self, authenticated_client: AsyncClient, test_user, test_db: AsyncSession):
        """Test listing personality templates."""
        # Seed a template directly in DB (since test DB doesn't run Alembic migrations)
        for i, name in enumerate(["Coach", "Begleiter", "Assistent", "Cheerleader"]):
            template = PersonalityTemplate(
                name=name,
                description=f"Beschreibung fuer {name}",
                traits={"formality": 50, "humor": 50, "strictness": 50, "empathy": 50, "verbosity": 50},
                is_default=(i == 0),
            )
            test_db.add(template)
        await test_db.commit()

        response = await authenticated_client.get("/api/v1/personality/templates")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 4

        # Check template structure
        template = data[0]
        assert "id" in template
        assert "name" in template
        assert "description" in template
        assert "traits" in template
        assert "is_default" in template
        assert "created_at" in template

    async def test_templates_have_traits(self, authenticated_client: AsyncClient, test_user, test_db: AsyncSession):
        """Test that templates have proper trait values."""
        template = PersonalityTemplate(
            name="Trait Test",
            description="Template mit Traits",
            traits={"formality": 80, "humor": 20, "strictness": 90, "empathy": 40, "verbosity": 30},
            is_default=False,
        )
        test_db.add(template)
        await test_db.commit()

        response = await authenticated_client.get("/api/v1/personality/templates")

        assert response.status_code == 200
        data = response.json()

        # Find our template
        trait_template = next(t for t in data if t["name"] == "Trait Test")
        assert trait_template["traits"]["formality"] == 80
        assert trait_template["traits"]["humor"] == 20
        assert trait_template["traits"]["strictness"] == 90
        assert trait_template["traits"]["empathy"] == 40
        assert trait_template["traits"]["verbosity"] == 30


class TestPersonalityAuth:
    """Tests for personality endpoints without authentication."""

    async def test_personality_unauthorized_profiles(self, client: AsyncClient):
        """Test listing profiles without token returns 403."""
        response = await client.get("/api/v1/personality/profiles")
        assert response.status_code == 403

    async def test_personality_unauthorized_create(self, client: AsyncClient):
        """Test creating a profile without token returns 403."""
        response = await client.post(
            "/api/v1/personality/profiles",
            json={"name": "No auth"},
        )
        assert response.status_code == 403

    async def test_personality_unauthorized_templates(self, client: AsyncClient):
        """Test listing templates without token returns 403."""
        response = await client.get("/api/v1/personality/templates")
        assert response.status_code == 403
