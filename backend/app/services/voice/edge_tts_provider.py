"""Edge-TTS free provider implementation."""
import io
import logging

import edge_tts

from app.services.voice.tts_base import TTSProvider


logger = logging.getLogger(__name__)


class EdgeTTSProvider(TTSProvider):
    """Edge-TTS free Text-to-Speech provider."""

    # Default German female voice
    DEFAULT_VOICE = "de-DE-KatjaNeural"

    async def synthesize(self, text: str, voice_id: str | None = None) -> bytes:
        """Synthesize text to audio using Edge-TTS.

        Args:
            text: Text to synthesize
            voice_id: Optional voice identifier (default: de-DE-KatjaNeural)

        Returns:
            Audio bytes (mp3)

        Raises:
            ValueError: If synthesis fails
        """
        voice = voice_id or self.DEFAULT_VOICE

        try:
            communicate = edge_tts.Communicate(text, voice)
            buffer = io.BytesIO()

            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    buffer.write(chunk["data"])

            audio_data = buffer.getvalue()

            if not audio_data:
                raise ValueError("Edge-TTS returned empty audio data")

            return audio_data

        except Exception as e:
            logger.error("Edge-TTS synthesis failed: %s", e)
            raise ValueError("Edge-TTS synthesis failed") from e
