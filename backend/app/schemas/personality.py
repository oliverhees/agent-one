"""Personality schemas for request/response validation."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator


class TraitsSchema(BaseModel):
    """Schema for personality traits (slider values 0-100)."""

    formality: int = Field(50, ge=0, le=100, description="Formality level (0=casual, 100=formal)")
    humor: int = Field(50, ge=0, le=100, description="Humor level (0=serious, 100=humorous)")
    strictness: int = Field(50, ge=0, le=100, description="Strictness level (0=lenient, 100=strict)")
    empathy: int = Field(50, ge=0, le=100, description="Empathy level (0=neutral, 100=empathetic)")
    verbosity: int = Field(50, ge=0, le=100, description="Verbosity level (0=concise, 100=verbose)")


class PersonalityProfileCreate(BaseModel):
    """Schema for creating a new personality profile."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Profile name",
        examples=["Mein Coach"],
    )

    template_id: UUID | None = Field(
        None,
        description="Template ID to base this profile on",
    )

    traits: dict[str, int] | None = Field(
        None,
        description="Personality traits (formality, humor, strictness, empathy, verbosity)",
    )

    rules: list[dict[str, Any]] | None = Field(
        None,
        description="Custom rules array",
    )

    custom_instructions: str | None = Field(
        None,
        max_length=5000,
        description="Free-text additional instructions",
        examples=["Sprich mich immer mit Du an"],
    )


class PersonalityProfileUpdate(BaseModel):
    """Schema for updating an existing personality profile."""

    name: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Profile name",
    )

    traits: dict[str, int] | None = Field(
        None,
        description="Personality traits",
    )

    rules: list[dict[str, Any]] | None = Field(
        None,
        description="Custom rules array",
    )

    voice_style: dict[str, Any] | None = Field(
        None,
        description="Voice configuration (TTS parameters)",
    )

    custom_instructions: str | None = Field(
        None,
        max_length=5000,
        description="Free-text additional instructions",
    )


class PersonalityProfileResponse(BaseModel):
    """Schema for personality profile response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Profile unique identifier")
    user_id: UUID = Field(..., description="User who owns this profile")
    name: str = Field(..., description="Profile name")
    is_active: bool = Field(..., description="Is this the active profile?")
    template_id: UUID | None = Field(None, description="Base template ID")
    traits: dict[str, Any] = Field(default_factory=dict, description="Personality traits")
    rules: list[dict[str, Any]] = Field(default_factory=list, description="Custom rules")
    voice_style: dict[str, Any] = Field(default_factory=dict, description="Voice configuration")
    custom_instructions: str | None = Field(None, description="Additional instructions")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class PersonalityTemplateResponse(BaseModel):
    """Schema for personality template response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Template unique identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    traits: dict[str, Any] = Field(..., description="Predefined trait values")
    rules: list[dict[str, Any]] = Field(default_factory=list, description="Predefined rules")
    is_default: bool = Field(..., description="Is this the default template?")
    icon: str | None = Field(None, description="Icon identifier")
    created_at: datetime = Field(..., description="Creation timestamp")
