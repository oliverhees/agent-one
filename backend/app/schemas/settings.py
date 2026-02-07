"""ADHS settings schemas for request/response validation."""

import re

from pydantic import BaseModel, Field, field_validator


TIME_PATTERN = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class ADHSSettingsResponse(BaseModel):
    """Schema for ADHS settings response."""

    adhs_mode: bool = Field(..., description="ADHS mode enabled?")
    nudge_intensity: str = Field(..., description="Nudge intensity: low, medium, high")
    auto_breakdown: bool = Field(..., description="Suggest auto task breakdown for large tasks?")
    gamification_enabled: bool = Field(..., description="Gamification system enabled?")
    focus_timer_minutes: int = Field(..., description="Default focus timer duration in minutes")
    quiet_hours_start: str = Field(..., description="Quiet hours start (HH:MM)")
    quiet_hours_end: str = Field(..., description="Quiet hours end (HH:MM)")
    preferred_reminder_times: list[str] = Field(..., description="Preferred reminder times (HH:MM)")


class ADHSSettingsUpdate(BaseModel):
    """Schema for updating ADHS settings (partial update)."""

    adhs_mode: bool | None = Field(None, description="ADHS mode on/off")
    nudge_intensity: str | None = Field(None, description="Nudge intensity: low, medium, high")
    auto_breakdown: bool | None = Field(None, description="Auto breakdown on/off")
    gamification_enabled: bool | None = Field(None, description="Gamification on/off")
    focus_timer_minutes: int | None = Field(None, ge=5, le=120, description="Focus timer duration (5-120 min)")
    quiet_hours_start: str | None = Field(None, description="Quiet hours start (HH:MM)")
    quiet_hours_end: str | None = Field(None, description="Quiet hours end (HH:MM)")
    preferred_reminder_times: list[str] | None = Field(None, max_length=10, description="Preferred reminder times")

    @field_validator("nudge_intensity")
    @classmethod
    def validate_nudge_intensity(cls, v: str | None) -> str | None:
        if v is not None and v not in ("low", "medium", "high"):
            raise ValueError("nudge_intensity must be 'low', 'medium', or 'high'")
        return v

    @field_validator("quiet_hours_start", "quiet_hours_end")
    @classmethod
    def validate_time_format(cls, v: str | None) -> str | None:
        if v is not None and not TIME_PATTERN.match(v):
            raise ValueError("Time must be in HH:MM format (e.g. '22:00')")
        return v

    @field_validator("preferred_reminder_times")
    @classmethod
    def validate_reminder_times(cls, v: list[str] | None) -> list[str] | None:
        if v is not None:
            for t in v:
                if not TIME_PATTERN.match(t):
                    raise ValueError(f"Invalid time format: '{t}'. Must be HH:MM.")
        return v
