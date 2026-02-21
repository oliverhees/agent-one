"""Voice live conversation WebSocket endpoint."""
import asyncio
import base64
import io
import json
import logging
import struct
import time
import wave
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query

from app.core.database import get_async_session
from app.core.security import verify_token
from app.services.voice.factory import get_stt_provider, get_tts_provider
from app.services.chat import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Voice Live"])

# Voice Activity Detection tuned for ~500ms chunks from mobile
SILENCE_THRESHOLD = 500  # RMS threshold (int16 audio)
SILENCE_CHUNKS_REQUIRED = 3  # ~1.5s of silence at 500ms chunks
MIN_AUDIO_LENGTH = 8000  # Minimum PCM bytes before processing (~250ms of 16kHz mono)

WAV_HEADER_SIZE = 44  # Standard WAV header size
SAMPLE_RATE = 16000
CHANNELS = 1
SAMPLE_WIDTH = 2  # 16-bit = 2 bytes


def calculate_rms(pcm_data: bytes) -> float:
    """Calculate RMS volume of int16 PCM audio (no WAV header)."""
    if len(pcm_data) < 2:
        return 0.0
    # Ensure even number of bytes
    usable = len(pcm_data) - (len(pcm_data) % 2)
    if usable < 2:
        return 0.0
    samples = struct.unpack(f"<{usable // 2}h", pcm_data[:usable])
    if not samples:
        return 0.0
    rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
    return rms


def strip_wav_header(wav_data: bytes) -> bytes:
    """Strip WAV header and return raw PCM data."""
    if len(wav_data) <= WAV_HEADER_SIZE:
        return wav_data
    # Check for RIFF header
    if wav_data[:4] == b"RIFF":
        return wav_data[WAV_HEADER_SIZE:]
    return wav_data


async def decode_audio_to_pcm(audio_data: bytes, audio_format: str) -> bytes:
    """Convert any audio format to raw PCM 16-bit 16kHz mono.

    For WAV: strips header directly (fast).
    For M4A/other: uses ffmpeg subprocess (safe, no shell).
    """
    if audio_format == "wav":
        return strip_wav_header(audio_data)

    # Use ffmpeg for non-WAV formats (M4A, AAC, etc.)
    # Note: create_subprocess_exec passes args as list (no shell injection)
    try:
        proc = await asyncio.create_subprocess_exec(
            "ffmpeg", "-i", "pipe:0",
            "-f", "s16le", "-ar", str(SAMPLE_RATE), "-ac", str(CHANNELS),
            "-loglevel", "error",
            "pipe:1",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate(input=audio_data)
        if proc.returncode != 0:
            logger.warning("ffmpeg decode failed (rc=%d): %s",
                           proc.returncode, stderr.decode()[:200])
            return b""
        return stdout
    except FileNotFoundError:
        logger.error("ffmpeg not found - cannot decode %s audio", audio_format)
        return b""
    except Exception as e:
        logger.error("ffmpeg decode error: %s", e)
        return b""


def create_wav_from_pcm(pcm_data: bytes) -> bytes:
    """Create a valid WAV file from raw PCM data."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_data)
    return buf.getvalue()


@router.websocket("/live")
async def voice_live(
    websocket: WebSocket,
    token: str = Query(...),
    wake_word: bool = Query(False),
):
    """
    WebSocket endpoint for live voice conversation with ALICE.

    Protocol:
    - Client sends JSON: {"type": "audio", "data": "<base64 WAV>", "format": "wav"}
    - Client can also send binary audio chunks (PCM 16-bit, 16kHz, mono)
    - Server detects speech pauses via RMS-based VAD
    - On pause: transcribe → ALICE → synthesize → send back
    - Server sends JSON: {"type": "transcript", "role": "user"|"assistant", "text": "..."}
    - Server sends JSON: {"type": "audio_response", "data": "<base64 MP3>"}
    - Server sends JSON: {"type": "status", "status": "listening"|"thinking"|"speaking"}
    - Client sends JSON: {"type": "end"} to close session

    Auth via query param: ?token=JWT_TOKEN
    """
    # Authenticate
    try:
        payload = verify_token(token)
        user_id = UUID(payload["sub"])
    except Exception:
        await websocket.close(code=4001, reason="Unauthorized")
        return

    await websocket.accept()
    logger.info("Voice live session started for user %s", user_id)

    # Get DB session
    async with get_async_session() as db:
        try:
            # Initialize providers
            stt = await get_stt_provider(db, user_id)
            tts = await get_tts_provider(db, user_id)
            logger.info("Voice providers initialized: STT=%s, TTS=%s",
                        type(stt).__name__, type(tts).__name__)

            # Initialize chat service for ALICE responses
            chat_service = ChatService(db)

            # Each voice session gets its own conversation for clean context.
            # Cross-session memory is handled by _get_recent_conversation_context.
            conversation = await chat_service.create_conversation(
                user_id=user_id,
                title="Live-Gespraech"
            )

            # Send conversation ID to client so it can navigate to it after session
            await websocket.send_json({
                "type": "session_start",
                "conversation_id": str(conversation.id),
            })

            # Voice Greeting bei Wake Word Detection
            if wake_word:
                try:
                    from app.models.user import User
                    user = await db.get(User, user_id)
                    display_name = user.display_name if user else "du"
                    greeting = f"Hallo {display_name}, ich bin da! Was kann ich fuer dich tun?"

                    await websocket.send_json({
                        "type": "status",
                        "status": "speaking"
                    })

                    await websocket.send_json({
                        "type": "transcript",
                        "role": "assistant",
                        "text": greeting
                    })

                    try:
                        audio_greeting = await tts.synthesize(greeting)
                        await websocket.send_bytes(audio_greeting)
                    except Exception as e:
                        logger.warning("TTS for greeting failed: %s", e)
                except Exception as e:
                    logger.error("Wake word greeting failed: %s", e)

            # Raw PCM audio buffer (no WAV headers) and silence tracking
            pcm_buffer = bytearray()
            silence_count = 0
            is_processing = False
            chunk_count = 0

            # Send initial status
            await websocket.send_json({
                "type": "status",
                "status": "listening"
            })

            while True:
                try:
                    data = await asyncio.wait_for(
                        websocket.receive(),
                        timeout=300.0  # 5 minute timeout
                    )
                except asyncio.TimeoutError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Session timed out"
                    })
                    break

                # Extract raw PCM from incoming data
                pcm_chunk = None
                audio_format = "wav"  # default

                if "bytes" in data:
                    # Binary audio chunk (direct binary WebSocket)
                    raw = data["bytes"]
                    pcm_chunk = await decode_audio_to_pcm(raw, "wav")

                elif "text" in data:
                    try:
                        msg = json.loads(data["text"])

                        if msg.get("type") == "end":
                            logger.info("Client requested session end")
                            break

                        if msg.get("type") == "audio_complete" and msg.get("data"):
                            # Complete utterance from client-side VAD
                            # Send directly to Whisper (no server-side VAD needed)
                            if is_processing:
                                continue
                            is_processing = True

                            raw = base64.b64decode(msg["data"])
                            audio_format = msg.get("format", "m4a")
                            logger.info("Received complete utterance: %d bytes (%s)",
                                        len(raw), audio_format)

                            try:
                                await websocket.send_json({
                                    "type": "status",
                                    "status": "thinking"
                                })

                                # Map format to MIME type (Whisper handles M4A natively)
                                mime_map = {
                                    "m4a": "audio/m4a",
                                    "wav": "audio/wav",
                                    "mp3": "audio/mpeg",
                                    "webm": "audio/webm",
                                }
                                mime_type = mime_map.get(audio_format, f"audio/{audio_format}")

                                # STT: Send audio directly to Whisper (no ffmpeg needed)
                                t0 = time.monotonic()
                                user_text = await stt.transcribe(raw, mime_type)
                                t_stt = time.monotonic() - t0
                                logger.info("[TIMING] STT: %.2fs | result: '%s'",
                                            t_stt, user_text[:80] if user_text else "(empty)")

                                if user_text.strip():
                                    await websocket.send_json({
                                        "type": "transcript",
                                        "role": "user",
                                        "text": user_text
                                    })

                                    # Callback: speak intermediate text immediately (e.g. "Moment, ich mache das!")
                                    async def on_intermediate(text):
                                        logger.info("[VOICE] Intermediate: '%s'", text[:80])
                                        await websocket.send_json({
                                            "type": "transcript",
                                            "role": "assistant",
                                            "text": text
                                        })
                                        await websocket.send_json({
                                            "type": "status",
                                            "status": "speaking"
                                        })
                                        try:
                                            audio = await tts.synthesize(text)
                                            await websocket.send_bytes(audio)
                                        except Exception as e:
                                            logger.warning("Intermediate TTS failed: %s", e)
                                        # Back to thinking while tool executes
                                        await websocket.send_json({
                                            "type": "status",
                                            "status": "thinking"
                                        })

                                    t1 = time.monotonic()
                                    alice_response = await chat_service.send_message_voice(
                                        user_id=user_id,
                                        conversation_id=conversation.id,
                                        content=user_text,
                                        on_intermediate_text=on_intermediate,
                                    )
                                    t_llm = time.monotonic() - t1
                                    logger.info("[TIMING] LLM: %.2fs | response: '%s'",
                                                t_llm, alice_response[:80] if alice_response else "(empty)")

                                    await websocket.send_json({
                                        "type": "transcript",
                                        "role": "assistant",
                                        "text": alice_response
                                    })

                                    await websocket.send_json({
                                        "type": "status",
                                        "status": "speaking"
                                    })

                                    try:
                                        t2 = time.monotonic()
                                        audio_response = await tts.synthesize(alice_response)
                                        t_tts = time.monotonic() - t2
                                        await websocket.send_bytes(audio_response)
                                        t_total = time.monotonic() - t0
                                        logger.info("[TIMING] TTS: %.2fs | audio: %d bytes | TOTAL: %.2fs (STT:%.1f + LLM:%.1f + TTS:%.1f)",
                                                    t_tts, len(audio_response), t_total, t_stt, t_llm, t_tts)
                                    except Exception as e:
                                        logger.warning("TTS failed: %s", e)
                                else:
                                    logger.info("STT returned empty text, ignoring")

                            except Exception as e:
                                logger.error("Processing error: %s", e, exc_info=True)
                                await websocket.send_json({
                                    "type": "error",
                                    "message": "Verarbeitung fehlgeschlagen"
                                })
                            finally:
                                is_processing = False
                                await websocket.send_json({
                                    "type": "status",
                                    "status": "listening"
                                })

                            continue  # Skip chunk-based VAD

                        if msg.get("type") == "audio" and msg.get("data"):
                            # Base64-encoded audio chunks (legacy fallback)
                            raw = base64.b64decode(msg["data"])
                            audio_format = msg.get("format", "wav")
                            pcm_chunk = await decode_audio_to_pcm(raw, audio_format)

                    except (json.JSONDecodeError, Exception) as e:
                        logger.warning("Failed to parse message: %s", e)
                        continue

                if pcm_chunk is None:
                    continue

                if is_processing:
                    continue  # Skip while processing

                chunk_count += 1
                rms = calculate_rms(pcm_chunk)

                if chunk_count <= 3 or chunk_count % 20 == 0:
                    logger.info("Audio chunk #%d: %d bytes PCM, RMS=%.1f (format=%s)",
                                chunk_count, len(pcm_chunk), rms, audio_format)

                if rms > SILENCE_THRESHOLD:
                    # Speech detected
                    pcm_buffer.extend(pcm_chunk)
                    silence_count = 0
                else:
                    # Silence detected
                    silence_count += 1
                    pcm_buffer.extend(pcm_chunk)

                    if silence_count >= SILENCE_CHUNKS_REQUIRED and len(pcm_buffer) > MIN_AUDIO_LENGTH:
                        # Speech pause detected - process the audio
                        is_processing = True
                        accumulated_pcm = bytes(pcm_buffer)
                        pcm_buffer.clear()
                        silence_count = 0

                        logger.info("Speech pause detected. Processing %d bytes of PCM audio",
                                    len(accumulated_pcm))

                        try:
                            # Status: thinking
                            await websocket.send_json({
                                "type": "status",
                                "status": "thinking"
                            })

                            # Create proper WAV from accumulated PCM
                            wav_data = create_wav_from_pcm(accumulated_pcm)

                            # STT: Audio → Text
                            user_text = await stt.transcribe(wav_data, "audio/wav")
                            logger.info("STT result: '%s'", user_text[:100] if user_text else "(empty)")

                            if user_text.strip():
                                # Send user transcript
                                await websocket.send_json({
                                    "type": "transcript",
                                    "role": "user",
                                    "text": user_text
                                })

                                # ALICE: Text → Response
                                alice_response = await chat_service.send_message_voice(
                                    user_id=user_id,
                                    conversation_id=conversation.id,
                                    content=user_text
                                )
                                logger.info("ALICE response: '%s'",
                                            alice_response[:100] if alice_response else "(empty)")

                                # Send assistant transcript
                                await websocket.send_json({
                                    "type": "transcript",
                                    "role": "assistant",
                                    "text": alice_response
                                })

                                # Status: speaking
                                await websocket.send_json({
                                    "type": "status",
                                    "status": "speaking"
                                })

                                # TTS: Text → Audio → send as binary
                                try:
                                    audio_response = await tts.synthesize(alice_response)
                                    await websocket.send_bytes(audio_response)
                                    logger.info("TTS audio sent: %d bytes", len(audio_response))
                                except Exception as e:
                                    logger.warning("TTS failed: %s", e)
                                    # Continue without audio - text is already sent
                            else:
                                logger.info("STT returned empty text, ignoring")

                        except Exception as e:
                            logger.error("Processing error: %s", e, exc_info=True)
                            await websocket.send_json({
                                "type": "error",
                                "message": "Verarbeitung fehlgeschlagen"
                            })
                        finally:
                            is_processing = False
                            await websocket.send_json({
                                "type": "status",
                                "status": "listening"
                            })

        except WebSocketDisconnect:
            logger.info("Voice live session disconnected for user %s", user_id)
        except Exception as e:
            logger.error("Voice live session error: %s", e, exc_info=True)
        finally:
            logger.info("Voice live session ended for user %s (chunks received: %d)",
                        user_id, chunk_count if 'chunk_count' in dir() else 0)
