"""OpenAI TTS provider implementation."""
import logging

import httpx

from app.services.voice.tts_base import TTSProvider


logger = logging.getLogger(__name__)


class OpenAITTS(TTSProvider):
    """OpenAI Text-to-Speech provider."""

    DEFAULT_VOICE = "nova"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"

    async def synthesize(self, text: str, voice_id: str | None = None) -> bytes:
        """Synthesize text to audio using OpenAI TTS API.

        Args:
            text: Text to synthesize
            voice_id: Optional voice identifier (default: nova)

        Returns:
            Audio bytes (mp3)

        Raises:
            ValueError: If synthesis fails or API key is missing
        """
        voice = voice_id or self.DEFAULT_VOICE

        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/audio/speech",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": "tts-1",
                        "input": text,
                        "voice": voice,
                    },
                )
                response.raise_for_status()

                audio_data = response.content
                if not audio_data:
                    raise ValueError("OpenAI TTS returned empty audio data")

                return audio_data

            except httpx.HTTPStatusError as e:
                logger.error("OpenAI TTS API error: %s - %s", e.response.status_code, e.response.text)
                raise ValueError(f"OpenAI TTS API error: {e.response.status_code}") from e
            except Exception as e:
                logger.error("OpenAI TTS request failed: %s", e)
                raise ValueError("OpenAI TTS request failed") from e
