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
    expo_push_token: str | None = Field(None, description="Expo push notification token")
    notifications_enabled: bool = Field(..., description="Push notifications enabled?")
    display_name: str | None = Field(None, description="User's display name for personalization")
    onboarding_complete: bool = Field(..., description="Has user completed onboarding?")


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
    notifications_enabled: bool | None = Field(None, description="Push notifications on/off")
    display_name: str | None = Field(None, min_length=1, max_length=100, description="User's display name")
    onboarding_complete: bool | None = Field(None, description="Onboarding completion status")

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


class OnboardingRequest(BaseModel):
    """Schema for onboarding completion request."""

    display_name: str | None = Field(None, min_length=1, max_length=100, description="User's display name (optional)")
    focus_timer_minutes: int | None = Field(None, ge=5, le=120, description="Preferred focus timer duration")
    nudge_intensity: str | None = Field(None, description="Preferred nudge intensity")

    @field_validator("nudge_intensity")
    @classmethod
    def validate_nudge_intensity(cls, v: str | None) -> str | None:
        if v is not None and v not in ("low", "medium", "high"):
            raise ValueError("nudge_intensity must be 'low', 'medium', or 'high'")
        return v


class OnboardingResponse(BaseModel):
    """Schema for onboarding completion response."""

    success: bool = Field(..., description="Whether onboarding was completed successfully")
    message: str = Field(..., description="Status message")


class ApiKeyUpdate(BaseModel):
    """Schema for updating API keys (partial update)."""

    anthropic: str | None = Field(None, min_length=1, description="Anthropic API key")
    elevenlabs: str | None = Field(None, min_length=1, description="ElevenLabs API key")
    deepgram: str | None = Field(None, min_length=1, description="Deepgram API key")


class ApiKeyResponse(BaseModel):
    """Schema for API keys response (masked)."""

    anthropic: str | None = Field(None, description="Anthropic API key (masked: ...XXXX)")
    elevenlabs: str | None = Field(None, description="ElevenLabs API key (masked: ...XXXX)")
    deepgram: str | None = Field(None, description="Deepgram API key (masked: ...XXXX)")
    system_anthropic_active: bool = Field(False, description="System Anthropic API key configured in .env?")


class VoiceProviderUpdate(BaseModel):
    """Schema for updating voice providers."""

    stt_provider: str | None = Field(None, description="STT provider: 'deepgram' or 'whisper'")
    tts_provider: str | None = Field(None, description="TTS provider: 'elevenlabs' or 'edge-tts'")

    @field_validator("stt_provider")
    @classmethod
    def validate_stt_provider(cls, v: str | None) -> str | None:
        if v is not None and v not in ("deepgram", "whisper"):
            raise ValueError("stt_provider must be 'deepgram' or 'whisper'")
        return v

    @field_validator("tts_provider")
    @classmethod
    def validate_tts_provider(cls, v: str | None) -> str | None:
        if v is not None and v not in ("elevenlabs", "edge-tts"):
            raise ValueError("tts_provider must be 'elevenlabs' or 'edge-tts'")
        return v


class VoiceProviderResponse(BaseModel):
    """Schema for voice providers response."""

    stt_provider: str = Field(..., description="Current STT provider")
    tts_provider: str = Field(..., description="Current TTS provider")
