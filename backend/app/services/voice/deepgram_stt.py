"""Deepgram STT provider implementation."""
import logging

import httpx

from app.services.voice.stt_base import STTProvider


logger = logging.getLogger(__name__)


class DeepgramSTT(STTProvider):
    """Deepgram Speech-to-Text provider."""

    def __init__(self, api_key: str):
        """Initialize Deepgram STT provider.

        Args:
            api_key: Deepgram API key
        """
        self.api_key = api_key
        self.base_url = "https://api.deepgram.com/v1"

    async def transcribe(self, audio_data: bytes, mime_type: str = "audio/wav") -> str:
        """Transcribe audio data to text using Deepgram API.

        Args:
            audio_data: Raw audio bytes
            mime_type: Audio MIME type

        Returns:
            Transcribed text

        Raises:
            ValueError: If API key is missing or API call fails
        """
        if not self.api_key:
            raise ValueError("Deepgram API key is required")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/listen",
                    headers={
                        "Authorization": f"Token {self.api_key}",
                        "Content-Type": mime_type,
                    },
                    params={
                        "model": "nova-2",
                        "language": "de",
                        "smart_format": "true",
                    },
                    content=audio_data,
                )
                response.raise_for_status()
                data = response.json()

                # Extract transcript from response
                transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
                return transcript.strip()

            except httpx.HTTPStatusError as e:
                logger.error("Deepgram API HTTP error: %s - %s", e.response.status_code, e.response.text)
                raise ValueError(f"Deepgram API error: {e.response.status_code}") from e
            except (KeyError, IndexError) as e:
                logger.error("Deepgram API response parsing error: %s", e)
                raise ValueError("Unexpected Deepgram API response format") from e
            except Exception as e:
                logger.error("Deepgram API request failed: %s", e)
                raise ValueError("Deepgram API request failed") from e
