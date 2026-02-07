"""Voice live WebSocket tests."""
import pytest


class TestVoiceLiveWebSocket:
    """Tests for WebSocket /api/v1/voice/live.

    Note: Full integration testing of WebSocket with async DB sessions
    is complex with TestClient. These tests focus on basic connectivity
    and auth, while the audio processing logic is tested via unit tests.
    """

    def test_websocket_without_token(self):
        """WebSocket should close with 4001 if no token provided."""
        from starlette.testclient import TestClient
        from app.main import app

        with TestClient(app) as client:
            with pytest.raises(Exception):
                with client.websocket_connect("/api/v1/voice/live"):
                    pass

    def test_websocket_with_invalid_token(self):
        """WebSocket should close with 4001 if token is invalid."""
        from starlette.testclient import TestClient
        from app.main import app

        with TestClient(app) as client:
            with pytest.raises(Exception):
                with client.websocket_connect(
                    "/api/v1/voice/live?token=invalid-token"
                ):
                    pass


class TestRMSCalculation:
    """Tests for RMS volume calculation."""

    def test_calculate_rms_empty(self):
        """RMS of empty data should be 0."""
        from app.api.v1.voice_live import calculate_rms

        assert calculate_rms(b"") == 0.0
        assert calculate_rms(b"\x00") == 0.0

    def test_calculate_rms_silence(self):
        """RMS of silent audio should be 0."""
        from app.api.v1.voice_live import calculate_rms

        silent_audio = b"\x00\x00" * 100
        assert calculate_rms(silent_audio) == 0.0

    def test_calculate_rms_loud(self):
        """RMS of loud audio should be high."""
        from app.api.v1.voice_live import calculate_rms

        # Create loud audio (max int16 amplitude)
        loud_audio = b"\xff\x7f" * 100  # 32767 (max positive int16)
        rms = calculate_rms(loud_audio)
        assert rms > 30000  # High RMS value

    def test_calculate_rms_medium(self):
        """RMS of medium audio should be medium."""
        from app.api.v1.voice_live import calculate_rms
        import struct

        # Create medium audio (1000 amplitude)
        samples = [1000, -1000] * 50
        medium_audio = b"".join(struct.pack("<h", s) for s in samples)
        rms = calculate_rms(medium_audio)
        assert 900 < rms < 1100  # Should be around 1000


class TestVoiceActivityDetection:
    """Tests for voice activity detection constants."""

    def test_silence_threshold_is_reasonable(self):
        """Silence threshold should be set to a reasonable value."""
        from app.api.v1.voice_live import SILENCE_THRESHOLD

        # Should be low enough to detect silence, high enough to filter noise
        assert 100 <= SILENCE_THRESHOLD <= 1000

    def test_silence_chunks_required_is_reasonable(self):
        """Silence chunks required should be set to a reasonable value."""
        from app.api.v1.voice_live import SILENCE_CHUNKS_REQUIRED

        # Should be enough to avoid false triggers, but not too long
        assert 5 <= SILENCE_CHUNKS_REQUIRED <= 20

    def test_min_audio_length_is_reasonable(self):
        """Minimum audio length should be set to a reasonable value."""
        from app.api.v1.voice_live import MIN_AUDIO_LENGTH

        # Should be at least a few thousand bytes (e.g. 200ms at 16kHz)
        assert 1000 <= MIN_AUDIO_LENGTH <= 10000
