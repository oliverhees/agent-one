"""Voice live conversation WebSocket endpoint."""
import asyncio
import json
import logging
import struct
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.core.security import verify_token
from app.services.voice.factory import get_stt_provider, get_tts_provider
from app.services.chat import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Voice Live"])

# Simple Voice Activity Detection: if incoming audio chunk RMS is below threshold
# for N consecutive chunks, we consider it a speech pause
SILENCE_THRESHOLD = 500  # RMS threshold (int16 audio)
SILENCE_CHUNKS_REQUIRED = 10  # ~1 second of silence at 100ms chunks
MIN_AUDIO_LENGTH = 3200  # Minimum audio bytes before processing (~200ms of 16kHz mono)


def calculate_rms(audio_data: bytes) -> float:
    """Calculate RMS volume of int16 PCM audio."""
    if len(audio_data) < 2:
        return 0.0
    samples = struct.unpack(f"<{len(audio_data) // 2}h", audio_data)
    if not samples:
        return 0.0
    rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
    return rms


@router.websocket("/live")
async def voice_live(
    websocket: WebSocket,
    token: str = Query(...),
):
    """
    WebSocket endpoint for live voice conversation with ALICE.

    Protocol:
    - Client sends binary audio chunks (PCM 16-bit, 16kHz, mono)
    - Server detects speech pauses
    - On pause: transcribe → ALICE → synthesize → send back
    - Server sends JSON messages: {"type": "transcript", "role": "user"|"assistant", "text": "..."}
    - Server sends binary audio chunks (MP3) for TTS playback
    - Server sends JSON: {"type": "status", "status": "listening"|"thinking"|"speaking"}

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

            # Initialize chat service for ALICE responses
            chat_service = ChatService(db)

            # Create or get conversation for this live session
            conversation = await chat_service.create_conversation(
                user_id=user_id,
                title="Live-Gespraech"
            )

            # Audio buffer and silence tracking
            audio_buffer = bytearray()
            silence_count = 0
            is_processing = False

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

                if "bytes" in data:
                    # Binary audio chunk
                    chunk = data["bytes"]

                    if is_processing:
                        continue  # Skip while processing

                    rms = calculate_rms(chunk)

                    if rms > SILENCE_THRESHOLD:
                        # Speech detected
                        audio_buffer.extend(chunk)
                        silence_count = 0
                    else:
                        # Silence detected
                        silence_count += 1
                        audio_buffer.extend(chunk)

                        if silence_count >= SILENCE_CHUNKS_REQUIRED and len(audio_buffer) > MIN_AUDIO_LENGTH:
                            # Speech pause detected - process the audio
                            is_processing = True
                            audio_data = bytes(audio_buffer)
                            audio_buffer.clear()
                            silence_count = 0

                            try:
                                # Status: thinking
                                await websocket.send_json({
                                    "type": "status",
                                    "status": "thinking"
                                })

                                # STT: Audio → Text
                                user_text = await stt.transcribe(audio_data, "audio/wav")

                                if user_text.strip():
                                    # Send user transcript
                                    await websocket.send_json({
                                        "type": "transcript",
                                        "role": "user",
                                        "text": user_text
                                    })

                                    # ALICE: Text → Response
                                    # Use the simple send_message which returns the full response
                                    alice_response = await chat_service.send_message_simple(
                                        user_id=user_id,
                                        conversation_id=conversation.id,
                                        content=user_text
                                    )

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

                                    # TTS: Text → Audio
                                    try:
                                        audio_response = await tts.synthesize(alice_response)
                                        await websocket.send_bytes(audio_response)
                                    except Exception as e:
                                        logger.warning("TTS failed: %s", e)
                                        # Continue without audio - text is already sent

                            except Exception as e:
                                logger.error("Processing error: %s", e)
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

                elif "text" in data:
                    # JSON control message
                    try:
                        msg = json.loads(data["text"])
                        if msg.get("type") == "end":
                            break
                    except json.JSONDecodeError:
                        pass

        except WebSocketDisconnect:
            logger.info("Voice live session disconnected for user %s", user_id)
        except Exception as e:
            logger.error("Voice live session error: %s", e)
        finally:
            logger.info("Voice live session ended for user %s", user_id)
