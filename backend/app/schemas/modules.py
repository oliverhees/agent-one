"""Module schemas for request/response validation."""

from typing import Any

from pydantic import BaseModel, Field, field_validator

from app.core.modules import ALWAYS_ACTIVE_MODULES, VALID_MODULE_NAMES


class ModuleInfoResponse(BaseModel):
    """Schema describing a single module and its current state for a user."""

    name: str = Field(..., description="Module identifier")
    label: str = Field(..., description="Display label (German)")
    icon: str = Field(..., description="Ionicon icon name")
    description: str = Field(..., description="Short module description")
    active: bool = Field(..., description="Whether the module is currently active for the user")
    config: dict[str, Any] = Field(default_factory=dict, description="Module configuration")


class ModulesResponse(BaseModel):
    """Schema for the full module listing response."""

    active_modules: list[str] = Field(..., description="List of active module names")
    available_modules: list[ModuleInfoResponse] = Field(
        ..., description="All available modules with metadata"
    )


class ModulesUpdate(BaseModel):
    """Schema for updating which modules are active.

    Validates that all module names are known and ensures that
    always-active modules (e.g. core) are included automatically.
    """

    active_modules: list[str] = Field(..., description="Module names to activate")

    @field_validator("active_modules")
    @classmethod
    def validate_and_ensure_core(cls, v: list[str]) -> list[str]:
        unknown = set(v) - VALID_MODULE_NAMES
        if unknown:
            raise ValueError(f"Unknown module(s): {', '.join(sorted(unknown))}")
        # Auto-add always-active modules
        for mod in ALWAYS_ACTIVE_MODULES:
            if mod not in v:
                v.append(mod)
        return v


class ModuleConfigUpdate(BaseModel):
    """Schema for updating a single module's configuration."""

    config: dict[str, Any] = Field(..., description="Configuration key-value pairs to set")
