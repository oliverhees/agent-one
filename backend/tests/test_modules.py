"""Tests for module constants and Pydantic schemas."""

import pytest
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
