"""ADHS settings endpoint tests."""

import pytest
from httpx import AsyncClient


# ===========================================================================
# Get Settings (GET /api/v1/settings/adhs)
# ===========================================================================

class TestGetSettings:
    """Tests for GET /api/v1/settings/adhs."""

    async def test_default_settings(self, authenticated_client: AsyncClient, test_user):
        """New user should get default ADHS settings."""
        response = await authenticated_client.get("/api/v1/settings/adhs")

        assert response.status_code == 200
        data = response.json()

        assert data["adhs_mode"] is True
        assert data["nudge_intensity"] == "medium"
        assert data["auto_breakdown"] is True
        assert data["gamification_enabled"] is True
        assert data["focus_timer_minutes"] == 25
        assert data["quiet_hours_start"] == "22:00"
        assert data["quiet_hours_end"] == "07:00"
        assert isinstance(data["preferred_reminder_times"], list)
        assert len(data["preferred_reminder_times"]) == 3

    async def test_get_unauthorized(self, client: AsyncClient):
        """403 without auth."""
        response = await client.get("/api/v1/settings/adhs")
        assert response.status_code == 403


# ===========================================================================
# Update Settings (PUT /api/v1/settings/adhs)
# ===========================================================================

class TestUpdateSettings:
    """Tests for PUT /api/v1/settings/adhs."""

    async def test_partial_update_nudge_intensity(
        self, authenticated_client: AsyncClient, test_user
    ):
        """Partial update should only change the specified field."""
        response = await authenticated_client.put(
            "/api/v1/settings/adhs",
            json={"nudge_intensity": "high"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["nudge_intensity"] == "high"
        # Other fields unchanged
        assert data["adhs_mode"] is True
        assert data["focus_timer_minutes"] == 25

    async def test_update_focus_timer(self, authenticated_client: AsyncClient, test_user):
        """Update focus_timer_minutes."""
        response = await authenticated_client.put(
            "/api/v1/settings/adhs",
            json={"focus_timer_minutes": 15},
        )

        assert response.status_code == 200
        assert response.json()["focus_timer_minutes"] == 15

    async def test_update_quiet_hours(self, authenticated_client: AsyncClient, test_user):
        """Update quiet_hours_start and end."""
        response = await authenticated_client.put(
            "/api/v1/settings/adhs",
            json={"quiet_hours_start": "21:00", "quiet_hours_end": "08:00"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["quiet_hours_start"] == "21:00"
        assert data["quiet_hours_end"] == "08:00"

    async def test_update_adhs_mode_off(self, authenticated_client: AsyncClient, test_user):
        """Should be able to turn off ADHS mode."""
        response = await authenticated_client.put(
            "/api/v1/settings/adhs",
            json={"adhs_mode": False},
        )

        assert response.status_code == 200
        assert response.json()["adhs_mode"] is False

    async def test_update_preferred_reminder_times(
        self, authenticated_client: AsyncClient, test_user
    ):
        """Update preferred_reminder_times."""
        response = await authenticated_client.put(
            "/api/v1/settings/adhs",
            json={"preferred_reminder_times": ["08:00", "12:00", "17:00", "20:00"]},
        )

        assert response.status_code == 200
        assert response.json()["preferred_reminder_times"] == ["08:00", "12:00", "17:00", "20:00"]

    async def test_update_unauthorized(self, client: AsyncClient):
        """403 without auth."""
        response = await client.put(
            "/api/v1/settings/adhs",
            json={"nudge_intensity": "low"},
        )
        assert response.status_code == 403


# ===========================================================================
# Validation
# ===========================================================================

class TestSettingsValidation:
    """Tests for settings validation."""

    async def test_invalid_nudge_intensity(self, authenticated_client: AsyncClient, test_user):
        """nudge_intensity must be low/medium/high."""
        response = await authenticated_client.put(
            "/api/v1/settings/adhs",
            json={"nudge_intensity": "extreme"},
        )
        assert response.status_code == 422

    async def test_focus_timer_too_low(self, authenticated_client: AsyncClient, test_user):
        """focus_timer_minutes must be >= 5."""
        response = await authenticated_client.put(
            "/api/v1/settings/adhs",
            json={"focus_timer_minutes": 2},
        )
        assert response.status_code == 422

    async def test_focus_timer_too_high(self, authenticated_client: AsyncClient, test_user):
        """focus_timer_minutes must be <= 120."""
        response = await authenticated_client.put(
            "/api/v1/settings/adhs",
            json={"focus_timer_minutes": 200},
        )
        assert response.status_code == 422

    async def test_invalid_quiet_hours_format(self, authenticated_client: AsyncClient, test_user):
        """quiet_hours_start must be HH:MM format."""
        response = await authenticated_client.put(
            "/api/v1/settings/adhs",
            json={"quiet_hours_start": "9pm"},
        )
        assert response.status_code == 422

    async def test_invalid_reminder_time_format(
        self, authenticated_client: AsyncClient, test_user
    ):
        """preferred_reminder_times must all be HH:MM."""
        response = await authenticated_client.put(
            "/api/v1/settings/adhs",
            json={"preferred_reminder_times": ["09:00", "noon"]},
        )
        assert response.status_code == 422


# ===========================================================================
# API Keys Management (GET/PUT /api/v1/settings/api-keys)
# ===========================================================================

class TestApiKeys:
    """Tests for API keys management."""

    async def test_get_api_keys_empty(self, authenticated_client: AsyncClient, test_user):
        """GET /api/v1/settings/api-keys returns None for all keys by default."""
        response = await authenticated_client.get("/api/v1/settings/api-keys")

        assert response.status_code == 200
        data = response.json()

        assert data["anthropic"] is None
        assert data["elevenlabs"] is None
        assert data["deepgram"] is None

    async def test_save_api_keys_all(self, authenticated_client: AsyncClient, test_user):
        """PUT /api/v1/settings/api-keys saves all provided keys."""
        response = await authenticated_client.put(
            "/api/v1/settings/api-keys",
            json={
                "anthropic": "sk-ant-api03-test123456789012345678901234567890",
                "elevenlabs": "el_test_key_abcdefghijklmnop",
                "deepgram": "dg_test_key_xyz9876543210",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Keys should be masked (last 4 characters)
        assert data["anthropic"] == "...7890"
        assert data["elevenlabs"] == "...mnop"
        assert data["deepgram"] == "...3210"

    async def test_save_api_keys_partial(self, authenticated_client: AsyncClient, test_user):
        """PUT /api/v1/settings/api-keys can update only one key."""
        # Save initial keys
        await authenticated_client.put(
            "/api/v1/settings/api-keys",
            json={"anthropic": "sk-ant-old-key-12345678"},
        )

        # Update only elevenlabs
        response = await authenticated_client.put(
            "/api/v1/settings/api-keys",
            json={"elevenlabs": "el_new_key_9999"},
        )

        assert response.status_code == 200
        data = response.json()

        # Old key preserved
        assert data["anthropic"] == "...5678"
        # New key saved
        assert data["elevenlabs"] == "...9999"
        # Unchanged
        assert data["deepgram"] is None

    async def test_get_api_keys_after_save(self, authenticated_client: AsyncClient, test_user):
        """GET /api/v1/settings/api-keys returns masked keys after save."""
        # Save keys
        await authenticated_client.put(
            "/api/v1/settings/api-keys",
            json={"anthropic": "sk-ant-secret-key-abcd1234"},
        )

        # Get keys
        response = await authenticated_client.get("/api/v1/settings/api-keys")

        assert response.status_code == 200
        data = response.json()

        assert data["anthropic"] == "...1234"
        assert data["elevenlabs"] is None
        assert data["deepgram"] is None

    async def test_api_keys_unauthorized(self, client: AsyncClient):
        """403 without auth."""
        response = await client.get("/api/v1/settings/api-keys")
        assert response.status_code == 403

        response = await client.put(
            "/api/v1/settings/api-keys",
            json={"anthropic": "sk-test"},
        )
        assert response.status_code == 403

    async def test_api_keys_validation_empty_string(
        self, authenticated_client: AsyncClient, test_user
    ):
        """Empty string should fail validation."""
        response = await authenticated_client.put(
            "/api/v1/settings/api-keys",
            json={"anthropic": ""},
        )
        assert response.status_code == 422


# ===========================================================================
# Voice Providers (GET/PUT /api/v1/settings/voice-providers)
# ===========================================================================

class TestVoiceProviders:
    """Tests for voice provider settings."""

    async def test_get_voice_providers_defaults(
        self, authenticated_client: AsyncClient, test_user
    ):
        """GET /api/v1/settings/voice-providers returns defaults."""
        response = await authenticated_client.get("/api/v1/settings/voice-providers")

        assert response.status_code == 200
        data = response.json()

        assert data["stt_provider"] == "deepgram"
        assert data["tts_provider"] == "elevenlabs"

    async def test_update_stt_provider(self, authenticated_client: AsyncClient, test_user):
        """PUT /api/v1/settings/voice-providers can update STT provider."""
        response = await authenticated_client.put(
            "/api/v1/settings/voice-providers",
            json={"stt_provider": "whisper"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["stt_provider"] == "whisper"
        # TTS unchanged
        assert data["tts_provider"] == "elevenlabs"

    async def test_update_tts_provider(self, authenticated_client: AsyncClient, test_user):
        """PUT /api/v1/settings/voice-providers can update TTS provider."""
        response = await authenticated_client.put(
            "/api/v1/settings/voice-providers",
            json={"tts_provider": "edge-tts"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["stt_provider"] == "deepgram"
        assert data["tts_provider"] == "edge-tts"

    async def test_update_both_providers(self, authenticated_client: AsyncClient, test_user):
        """PUT /api/v1/settings/voice-providers can update both at once."""
        response = await authenticated_client.put(
            "/api/v1/settings/voice-providers",
            json={"stt_provider": "whisper", "tts_provider": "edge-tts"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["stt_provider"] == "whisper"
        assert data["tts_provider"] == "edge-tts"

    async def test_invalid_stt_provider(self, authenticated_client: AsyncClient, test_user):
        """Invalid STT provider should fail validation."""
        response = await authenticated_client.put(
            "/api/v1/settings/voice-providers",
            json={"stt_provider": "unknown"},
        )
        assert response.status_code == 422

    async def test_invalid_tts_provider(self, authenticated_client: AsyncClient, test_user):
        """Invalid TTS provider should fail validation."""
        response = await authenticated_client.put(
            "/api/v1/settings/voice-providers",
            json={"tts_provider": "unknown"},
        )
        assert response.status_code == 422

    async def test_voice_providers_unauthorized(self, client: AsyncClient):
        """403 without auth."""
        response = await client.get("/api/v1/settings/voice-providers")
        assert response.status_code == 403

        response = await client.put(
            "/api/v1/settings/voice-providers",
            json={"stt_provider": "whisper"},
        )
        assert response.status_code == 403
