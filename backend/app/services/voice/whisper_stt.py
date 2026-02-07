"""Whisper (OpenAI) STT provider implementation."""
import logging

import httpx

from app.services.voice.stt_base import STTProvider


logger = logging.getLogger(__name__)


class WhisperSTT(STTProvider):
    """Whisper (OpenAI) Speech-to-Text provider."""

    def __init__(self, api_key: str):
        """Initialize Whisper STT provider.

        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key
        self.base_url = "https://api.openai.com/v1"

    async def transcribe(self, audio_data: bytes, mime_type: str = "audio/wav") -> str:
        """Transcribe audio data to text using OpenAI Whisper API.

        Args:
            audio_data: Raw audio bytes
            mime_type: Audio MIME type

        Returns:
            Transcribed text

        Raises:
            ValueError: If API key is missing or API call fails
        """
        if not self.api_key:
            raise ValueError("OpenAI API key is required")

        # Extract file extension from mime type
        extension_map = {
            "audio/wav": "wav",
            "audio/mpeg": "mp3",
            "audio/mp3": "mp3",
            "audio/webm": "webm",
            "audio/m4a": "m4a",
            "audio/x-m4a": "m4a",
            "audio/mp4": "m4a",
            "audio/ogg": "ogg",
        }
        extension = extension_map.get(mime_type, "wav")

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                files = {
                    "file": (f"audio.{extension}", audio_data, mime_type),
                    "model": (None, "whisper-1"),
                    "language": (None, "de"),
                }

                response = await client.post(
                    f"{self.base_url}/audio/transcriptions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                    },
                    files=files,
                )
                response.raise_for_status()
                data = response.json()

                # Extract transcript
                transcript = data["text"]
                return transcript.strip()

            except httpx.HTTPStatusError as e:
                logger.error("Whisper API HTTP error: %s - %s", e.response.status_code, e.response.text)
                raise ValueError(f"Whisper API error: {e.response.status_code}") from e
            except KeyError as e:
                logger.error("Whisper API response parsing error: %s", e)
                raise ValueError("Unexpected Whisper API response format") from e
            except Exception as e:
                logger.error("Whisper API request failed: %s", e)
                raise ValueError("Whisper API request failed") from e
