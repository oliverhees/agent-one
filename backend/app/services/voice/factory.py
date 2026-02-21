"""Factory for creating voice providers based on user settings."""
import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings as app_settings
from app.core.encryption import decrypt_value
from app.models.user_settings import UserSettings, DEFAULT_SETTINGS
from app.services.voice.stt_base import STTProvider
from app.services.voice.tts_base import TTSProvider

logger = logging.getLogger(__name__)


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

    provider_name = settings.get("stt_provider", "whisper")
    api_keys = settings.get("api_keys", {})

    if provider_name == "deepgram":
        from app.services.voice.deepgram_stt import DeepgramSTT

        # User key first, then system key
        encrypted_key = api_keys.get("deepgram")
        if encrypted_key:
            key = decrypt_value(encrypted_key)
            return DeepgramSTT(api_key=key)
        elif getattr(app_settings, "deepgram_api_key", None):
            return DeepgramSTT(api_key=app_settings.deepgram_api_key)
        else:
            # Fallback to Whisper if no Deepgram key available
            logger.info("No Deepgram API key found, falling back to Whisper (OpenAI)")
            provider_name = "whisper"

    if provider_name == "whisper":
        from app.services.voice.whisper_stt import WhisperSTT

        encrypted_key = api_keys.get("openai")
        if encrypted_key:
            key = decrypt_value(encrypted_key)
        elif getattr(app_settings, "openai_api_key", None):
            key = app_settings.openai_api_key
        else:
            raise ValueError(
                "Kein OpenAI API Key konfiguriert. "
                "Bitte unter Settings > API Keys einen OpenAI Key hinterlegen."
            )
        return WhisperSTT(api_key=key)

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
            return ElevenLabsTTS(api_key=key)
        # No ElevenLabs key → try OpenAI TTS, then Edge-TTS
        openai_key = api_keys.get("openai")
        if openai_key:
            from app.services.voice.openai_tts import OpenAITTS
            logger.info("No ElevenLabs key, falling back to OpenAI TTS")
            return OpenAITTS(api_key=decrypt_value(openai_key))
        if getattr(app_settings, "openai_api_key", None):
            from app.services.voice.openai_tts import OpenAITTS
            logger.info("No ElevenLabs key, falling back to OpenAI TTS (system key)")
            return OpenAITTS(api_key=app_settings.openai_api_key)
        from app.services.voice.edge_tts_provider import EdgeTTSProvider
        return EdgeTTSProvider()

    elif provider_name == "openai":
        from app.services.voice.openai_tts import OpenAITTS

        encrypted_key = api_keys.get("openai")
        if encrypted_key:
            key = decrypt_value(encrypted_key)
        elif getattr(app_settings, "openai_api_key", None):
            key = app_settings.openai_api_key
        else:
            # Fallback to free Edge-TTS
            logger.info("No OpenAI API key found for TTS, falling back to Edge-TTS")
            from app.services.voice.edge_tts_provider import EdgeTTSProvider
            return EdgeTTSProvider()
        return OpenAITTS(api_key=key)

    elif provider_name == "edge-tts":
        from app.services.voice.edge_tts_provider import EdgeTTSProvider

        return EdgeTTSProvider()

    else:
        raise ValueError(f"Unknown TTS provider: {provider_name}")
