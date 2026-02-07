"""Base class for Speech-to-Text providers."""
from abc import ABC, abstractmethod


class STTProvider(ABC):
    """Abstract base class for STT providers."""

    @abstractmethod
    async def transcribe(self, audio_data: bytes, mime_type: str = "audio/wav") -> str:
        """Transcribe audio data to text.

        Args:
            audio_data: Raw audio bytes
            mime_type: Audio MIME type (default: audio/wav)

        Returns:
            Transcribed text
        """
        ...
