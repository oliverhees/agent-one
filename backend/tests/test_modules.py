"""Tests for module constants, Pydantic schemas, and module service integration."""

import pytest
from httpx import AsyncClient
from pydantic import ValidationError

from app.core.modules import (
    ALL_MODULES,
    ALWAYS_ACTIVE_MODULES,
    DEFAULT_ACTIVE_MODULES,
    VALID_MODULE_NAMES,
)
from app.schemas.modules import (
    ModuleConfigUpdate,
    ModuleInfoResponse,
    ModulesResponse,
    ModulesUpdate,
)


# ===========================================================================
# Module Constants (app.core.modules)
# ===========================================================================

class TestModuleConstants:
    """Tests for module constant definitions."""

    def test_all_modules_defined(self):
        """ALL_MODULES must contain core, adhs, wellness, productivity."""
        expected = {"core", "adhs", "wellness", "productivity"}
        assert set(ALL_MODULES.keys()) == expected

    def test_core_module_is_always_active(self):
        """core must be in ALWAYS_ACTIVE_MODULES."""
        assert "core" in ALWAYS_ACTIVE_MODULES

    def test_always_active_modules_is_frozenset(self):
        """ALWAYS_ACTIVE_MODULES must be immutable."""
        assert isinstance(ALWAYS_ACTIVE_MODULES, frozenset)

    def test_module_has_required_fields(self):
        """Every module must have label, icon, description, default_config."""
        required_keys = {"label", "icon", "description", "default_config"}
        for name, meta in ALL_MODULES.items():
            assert required_keys.issubset(meta.keys()), (
                f"Module '{name}' is missing keys: {required_keys - meta.keys()}"
            )

    def test_default_active_modules(self):
        """DEFAULT_ACTIVE_MODULES must contain core and adhs."""
        assert "core" in DEFAULT_ACTIVE_MODULES
        assert "adhs" in DEFAULT_ACTIVE_MODULES

    def test_valid_module_names(self):
        """VALID_MODULE_NAMES must match ALL_MODULES keys."""
        assert VALID_MODULE_NAMES == frozenset(ALL_MODULES.keys())


# ===========================================================================
# Pydantic Schemas (app.schemas.modules)
# ===========================================================================

class TestModuleInfoResponse:
    """Tests for ModuleInfoResponse schema."""

    def test_module_info_response_creates_valid_instance(self):
        """ModuleInfoResponse should accept valid module data."""
        info = ModuleInfoResponse(
            name="adhs",
            label="ADHS-Coaching",
            icon="bulb-outline",
            description="Pattern-Erkennung, Nudges",
            active=True,
            config={"nudge_intensity": "medium"},
        )
        assert info.name == "adhs"
        assert info.label == "ADHS-Coaching"
        assert info.active is True
        assert info.config == {"nudge_intensity": "medium"}


class TestModulesResponse:
    """Tests for ModulesResponse schema."""

    def test_modules_response_creates_valid_instance(self):
        """ModulesResponse should accept active_modules and available_modules."""
        module_info = ModuleInfoResponse(
            name="core",
            label="Kern-Funktionen",
            icon="chatbubble-outline",
            description="Chat mit Alice",
            active=True,
            config={},
        )
        resp = ModulesResponse(
            active_modules=["core", "adhs"],
            available_modules=[module_info],
        )
        assert resp.active_modules == ["core", "adhs"]
        assert len(resp.available_modules) == 1
        assert resp.available_modules[0].name == "core"


class TestModulesUpdate:
    """Tests for ModulesUpdate schema with validation."""

    def test_modules_update_validates_module_names(self):
        """ModulesUpdate should accept valid module names."""
        update = ModulesUpdate(active_modules=["core", "adhs", "wellness"])
        assert "core" in update.active_modules
        assert "adhs" in update.active_modules
        assert "wellness" in update.active_modules

    def test_modules_update_rejects_unknown_module(self):
        """ModulesUpdate should reject unknown module names."""
        with pytest.raises(ValidationError) as exc_info:
            ModulesUpdate(active_modules=["core", "nonexistent"])
        assert "nonexistent" in str(exc_info.value)

    def test_modules_update_core_always_included(self):
        """ModulesUpdate should auto-add core if omitted."""
        update = ModulesUpdate(active_modules=["adhs"])
        assert "core" in update.active_modules


class TestModuleConfigUpdate:
    """Tests for ModuleConfigUpdate schema."""

    def test_module_config_update(self):
        """ModuleConfigUpdate should accept arbitrary config dict."""
        update = ModuleConfigUpdate(config={"nudge_intensity": "high", "auto_breakdown": False})
        assert update.config["nudge_intensity"] == "high"
        assert update.config["auto_breakdown"] is False

    def test_module_config_update_empty(self):
        """ModuleConfigUpdate should accept empty config."""
        update = ModuleConfigUpdate(config={})
        assert update.config == {}


# ===========================================================================
# Module Service Integration Tests (via HTTP endpoints)
# ===========================================================================

class TestModuleService:
    """Integration tests for module service methods via API endpoints."""

    async def test_get_modules_returns_defaults_for_new_user(
        self, authenticated_client: AsyncClient, test_user
    ):
        """GET /api/v1/settings/modules should return default modules for a new user."""
        response = await authenticated_client.get("/api/v1/settings/modules")

        assert response.status_code == 200
        data = response.json()

        assert "core" in data["active_modules"]
        assert "adhs" in data["active_modules"]
        assert len(data["available_modules"]) == 4

    async def test_get_modules_shows_active_status(
        self, authenticated_client: AsyncClient, test_user
    ):
        """Active flag should be True for active modules, False for inactive."""
        response = await authenticated_client.get("/api/v1/settings/modules")

        assert response.status_code == 200
        data = response.json()

        modules_by_name = {m["name"]: m for m in data["available_modules"]}

        assert modules_by_name["core"]["active"] is True
        assert modules_by_name["adhs"]["active"] is True
        assert modules_by_name["wellness"]["active"] is False
        assert modules_by_name["productivity"]["active"] is False

    async def test_activate_wellness_module(
        self, authenticated_client: AsyncClient, test_user
    ):
        """PUT /api/v1/settings/modules with wellness should activate it."""
        response = await authenticated_client.put(
            "/api/v1/settings/modules",
            json={"active_modules": ["core", "adhs", "wellness"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert "wellness" in data["active_modules"]
        modules_by_name = {m["name"]: m for m in data["available_modules"]}
        assert modules_by_name["wellness"]["active"] is True

    async def test_deactivate_adhs_module(
        self, authenticated_client: AsyncClient, test_user
    ):
        """PUT /api/v1/settings/modules with only core should deactivate adhs."""
        response = await authenticated_client.put(
            "/api/v1/settings/modules",
            json={"active_modules": ["core"]},
        )

        assert response.status_code == 200
        data = response.json()

        assert "adhs" not in data["active_modules"]
        modules_by_name = {m["name"]: m for m in data["available_modules"]}
        assert modules_by_name["adhs"]["active"] is False

    async def test_cannot_deactivate_core(
        self, authenticated_client: AsyncClient, test_user
    ):
        """PUT /api/v1/settings/modules without core should auto-add core."""
        response = await authenticated_client.put(
            "/api/v1/settings/modules",
            json={"active_modules": ["adhs"]},
        )

        assert response.status_code == 200
        data = response.json()

        # core should be auto-added by the schema validator
        assert "core" in data["active_modules"]

    async def test_invalid_module_name_rejected(
        self, authenticated_client: AsyncClient, test_user
    ):
        """PUT /api/v1/settings/modules with unknown module should return 422."""
        response = await authenticated_client.put(
            "/api/v1/settings/modules",
            json={"active_modules": ["core", "nonexistent"]},
        )

        assert response.status_code == 422

    async def test_update_module_config(
        self, authenticated_client: AsyncClient, test_user
    ):
        """PUT /api/v1/settings/modules/adhs/config should update config."""
        response = await authenticated_client.put(
            "/api/v1/settings/modules/adhs/config",
            json={"config": {"nudge_intensity": "high"}},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == "adhs"
        assert data["config"]["nudge_intensity"] == "high"

    async def test_update_config_preserves_existing_keys(
        self, authenticated_client: AsyncClient, test_user
    ):
        """Updating one config key should preserve other existing keys."""
        # Set first key
        await authenticated_client.put(
            "/api/v1/settings/modules/adhs/config",
            json={"config": {"nudge_intensity": "low"}},
        )

        # Set different key
        response = await authenticated_client.put(
            "/api/v1/settings/modules/adhs/config",
            json={"config": {"auto_breakdown": False}},
        )

        assert response.status_code == 200
        data = response.json()

        # Both keys should be present
        assert data["config"]["nudge_intensity"] == "low"
        assert data["config"]["auto_breakdown"] is False

    async def test_update_config_unknown_module_404(
        self, authenticated_client: AsyncClient, test_user
    ):
        """PUT /api/v1/settings/modules/nonexistent/config should return 404."""
        response = await authenticated_client.put(
            "/api/v1/settings/modules/nonexistent/config",
            json={"config": {"key": "value"}},
        )

        assert response.status_code == 404

    async def test_modules_unauthorized(self, client: AsyncClient):
        """GET /api/v1/settings/modules without auth should return 403."""
        response = await client.get("/api/v1/settings/modules")
        assert response.status_code == 403

    async def test_existing_adhs_settings_preserved(
        self, authenticated_client: AsyncClient, test_user
    ):
        """Activating a new module should not affect existing ADHS settings."""
        # Update ADHS settings first
        await authenticated_client.put(
            "/api/v1/settings/adhs",
            json={"nudge_intensity": "high", "focus_timer_minutes": 15},
        )

        # Activate wellness module
        await authenticated_client.put(
            "/api/v1/settings/modules",
            json={"active_modules": ["core", "adhs", "wellness"]},
        )

        # Verify ADHS settings are untouched
        response = await authenticated_client.get("/api/v1/settings/adhs")
        assert response.status_code == 200
        data = response.json()

        assert data["nudge_intensity"] == "high"
        assert data["focus_timer_minutes"] == 15
