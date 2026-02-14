"""Schemas for the memory/knowledge graph system."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConversationAnalysis(BaseModel):
    """Result of NLP analysis on a single conversation."""

    mood_score: float = Field(
        ...,
        ge=-1.0,
        le=1.0,
        description="Mood score from -1.0 (negative) to 1.0 (positive)",
    )

    energy_level: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Energy level from 0.0 (low) to 1.0 (high)",
    )

    focus_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Focus score from 0.0 (unfocused) to 1.0 (focused)",
    )

    detected_patterns: list[str] = Field(
        default_factory=list,
        description="ADHS patterns detected in conversation",
    )

    pattern_triggers: list[str] = Field(
        default_factory=list,
        description="Triggers observed for detected patterns",
    )

    notable_facts: list[str] = Field(
        default_factory=list,
        description="Notable facts about the user extracted from conversation",
    )


class PatternLogResponse(BaseModel):
    """Response schema for a single pattern log entry."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    conversation_id: UUID | None = None
    episode_id: str | None = None
    mood_score: float | None = None
    energy_level: float | None = None
    focus_score: float | None = None
    created_at: datetime


class MemoryStatusResponse(BaseModel):
    """Response schema for memory system status."""

    enabled: bool = Field(description="Whether memory/learning is enabled")
    total_episodes: int = Field(description="Total episodes processed")
    total_entities: int = Field(description="Total entities in knowledge graph")
    last_analysis_at: datetime | None = Field(
        None,
        description="Timestamp of last conversation analysis",
    )


class MemoryExportResponse(BaseModel):
    """Response schema for DSGVO Art. 15 data export."""

    entities: list[dict] = Field(description="All entities stored about the user")
    relations: list[dict] = Field(description="All relations in knowledge graph")
    pattern_logs: list[PatternLogResponse] = Field(
        description="All NLP analysis logs",
    )
    exported_at: datetime


class MemorySettingsUpdate(BaseModel):
    """Schema for updating memory settings."""

    enabled: bool = Field(description="Enable or disable memory/learning")
