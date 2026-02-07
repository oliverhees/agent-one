"""Base class for Text-to-Speech providers."""
from abc import ABC, abstractmethod


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""

    @abstractmethod
    async def synthesize(self, text: str, voice_id: str | None = None) -> bytes:
        """Synthesize text to audio.

        Args:
            text: Text to synthesize
            voice_id: Optional voice identifier

        Returns:
            Audio bytes (mp3)
        """
        ...
