"""Factory for creating voice providers based on user settings."""
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings as app_settings
from app.core.encryption import decrypt_value
from app.models.user_settings import UserSettings, DEFAULT_SETTINGS
from app.services.voice.stt_base import STTProvider
from app.services.voice.tts_base import TTSProvider


async def get_stt_provider(db: AsyncSession, user_id: UUID) -> STTProvider:
    """Get the configured STT provider for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Configured STT provider instance

    Raises:
        ValueError: If provider is unknown or API key is missing
    """
    # Load user settings
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    user_settings = result.scalar_one_or_none()
    settings = {**DEFAULT_SETTINGS, **(user_settings.settings if user_settings else {})}

    provider_name = settings.get("stt_provider", "deepgram")
    api_keys = settings.get("api_keys", {})

    if provider_name == "deepgram":
        from app.services.voice.deepgram_stt import DeepgramSTT

        # User key first, then system key
        encrypted_key = api_keys.get("deepgram")
        if encrypted_key:
            key = decrypt_value(encrypted_key)
        else:
            key = ""  # Will fail gracefully in provider
        return DeepgramSTT(api_key=key)

    elif provider_name == "whisper":
        from app.services.voice.whisper_stt import WhisperSTT

        key = app_settings.openai_api_key or ""
        return WhisperSTT(api_key=key)

    else:
        raise ValueError(f"Unknown STT provider: {provider_name}")


async def get_tts_provider(db: AsyncSession, user_id: UUID) -> TTSProvider:
    """Get the configured TTS provider for a user.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        Configured TTS provider instance

    Raises:
        ValueError: If provider is unknown or API key is missing
    """
    # Load user settings
    result = await db.execute(select(UserSettings).where(UserSettings.user_id == user_id))
    user_settings = result.scalar_one_or_none()
    settings = {**DEFAULT_SETTINGS, **(user_settings.settings if user_settings else {})}

    provider_name = settings.get("tts_provider", "elevenlabs")
    api_keys = settings.get("api_keys", {})

    if provider_name == "elevenlabs":
        from app.services.voice.elevenlabs_tts import ElevenLabsTTS

        encrypted_key = api_keys.get("elevenlabs")
        if encrypted_key:
            key = decrypt_value(encrypted_key)
        else:
            key = ""  # Will fail gracefully in provider
        return ElevenLabsTTS(api_key=key)

    elif provider_name == "edge-tts":
        from app.services.voice.edge_tts_provider import EdgeTTSProvider

        return EdgeTTSProvider()

    else:
        raise ValueError(f"Unknown TTS provider: {provider_name}")
