"""Schemas for the wellbeing monitoring system."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class WellbeingScoreResponse(BaseModel):
    """Response schema for a single wellbeing score calculation."""

    score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Wellbeing score from 0 (critical) to 100 (excellent)",
    )

    zone: str = Field(
        ...,
        description="Wellbeing zone: 'red' (critical), 'yellow' (warning), 'green' (good)",
    )

    components: dict[str, Any] = Field(
        default_factory=dict,
        description="Component scores that contribute to the overall score",
    )

    calculated_at: datetime = Field(
        ...,
        description="Timestamp when the score was calculated",
    )


class WellbeingHistoryResponse(BaseModel):
    """Response schema for wellbeing history over a time period."""

    scores: list[WellbeingScoreResponse] = Field(
        default_factory=list,
        description="List of wellbeing scores over the time period",
    )

    trend: str = Field(
        ...,
        description="Overall trend: 'rising', 'declining', or 'stable'",
    )

    average_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Average wellbeing score over the time period",
    )

    days: int = Field(
        ...,
        ge=1,
        description="Number of days in the history period",
    )


class InterventionResponse(BaseModel):
    """Response schema for a wellbeing intervention."""

    id: UUID = Field(
        ...,
        description="Unique intervention ID",
    )

    type: str = Field(
        ...,
        description="Type of intervention (e.g., 'proactive_check_in', 'crisis_support')",
    )

    trigger_pattern: str = Field(
        ...,
        description="Pattern that triggered the intervention",
    )

    message: str = Field(
        ...,
        description="Intervention message to display to the user",
    )

    status: str = Field(
        ...,
        description="Status of the intervention (e.g., 'pending', 'acknowledged', 'dismissed')",
    )

    created_at: datetime = Field(
        ...,
        description="Timestamp when the intervention was created",
    )


class InterventionAction(BaseModel):
    """Schema for user action on an intervention."""

    action: str = Field(
        ...,
        pattern=r"^(dismiss|act)$",
        description="Action to take: 'dismiss' or 'act'",
    )
