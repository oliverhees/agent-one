"""ElevenLabs TTS provider implementation."""
import logging

import httpx

from app.services.voice.tts_base import TTSProvider


logger = logging.getLogger(__name__)


class ElevenLabsTTS(TTSProvider):
    """ElevenLabs Text-to-Speech provider."""

    # Default German voice (Bella)
    DEFAULT_VOICE_ID = "EXAVITQu4vr4xnSDxMaL"

    def __init__(self, api_key: str):
        """Initialize ElevenLabs TTS provider.

        Args:
            api_key: ElevenLabs API key
        """
        self.api_key = api_key
        self.base_url = "https://api.elevenlabs.io/v1"

    async def synthesize(self, text: str, voice_id: str | None = None) -> bytes:
        """Synthesize text to audio using ElevenLabs API.

        Args:
            text: Text to synthesize
            voice_id: Optional voice identifier (default: Bella)

        Returns:
            Audio bytes (mp3)

        Raises:
            ValueError: If API key is missing or API call fails
        """
        if not self.api_key:
            raise ValueError("ElevenLabs API key is required")

        voice = voice_id or self.DEFAULT_VOICE_ID

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/text-to-speech/{voice}",
                    params={
                        "output_format": "mp3_22050_32",
                        "optimize_streaming_latency": "4",
                    },
                    headers={
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json",
                    },
                    json={
                        "text": text,
                        "model_id": "eleven_flash_v2_5",
                    },
                )
                response.raise_for_status()

                # Return raw audio bytes
                return response.content

            except httpx.HTTPStatusError as e:
                logger.error("ElevenLabs API HTTP error: %s - %s", e.response.status_code, e.response.text)
                raise ValueError(f"ElevenLabs API error: {e.response.status_code}") from e
            except Exception as e:
                logger.error("ElevenLabs API request failed: %s", e)
                raise ValueError("ElevenLabs API request failed") from e
