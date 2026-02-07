"""Voice endpoints for STT and TTS."""
import logging

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.rate_limit import standard_rate_limit
from app.models.user import User
from app.services.voice.factory import get_stt_provider, get_tts_provider


logger = logging.getLogger(__name__)
router = APIRouter(tags=["Voice"])


class TranscribeResponse(BaseModel):
    """Schema for transcription response."""

    text: str = Field(..., description="Transcribed text")


class SynthesizeRequest(BaseModel):
    """Schema for TTS synthesis request."""

    text: str = Field(..., min_length=1, max_length=5000, description="Text to synthesize")
    voice_id: str | None = Field(None, description="Optional voice ID")


@router.post(
    "/transcribe",
    response_model=TranscribeResponse,
    summary="Transcribe audio to text",
    dependencies=[Depends(standard_rate_limit)],
)
async def transcribe_audio(
    file: UploadFile = File(..., description="Audio file (wav, mp3, webm, m4a)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Transcribe uploaded audio file to text using the user's configured STT provider."""
    # Validate file type
    allowed_types = {
        "audio/wav",
        "audio/mpeg",
        "audio/mp3",
        "audio/webm",
        "audio/m4a",
        "audio/x-m4a",
        "audio/mp4",
        "audio/ogg",
    }
    content_type = file.content_type or "audio/wav"
    if content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio type: {content_type}. Allowed: wav, mp3, webm, m4a, ogg",
        )

    # Read audio data (max 25 MB)
    audio_data = await file.read()
    if len(audio_data) > 25 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Audio file too large (max 25 MB)")

    try:
        stt = await get_stt_provider(db, current_user.id)
        text = await stt.transcribe(audio_data, content_type)
        return TranscribeResponse(text=text)
    except ValueError as e:
        logger.error("STT transcription failed for user %s: %s", current_user.id, e)
        raise HTTPException(
            status_code=500,
            detail="Transkription fehlgeschlagen. Bitte prüfe deinen API Key.",
        ) from e
    except Exception as e:
        logger.error("Unexpected STT error for user %s: %s", current_user.id, e)
        raise HTTPException(
            status_code=500,
            detail="Transkription fehlgeschlagen.",
        ) from e


@router.post(
    "/synthesize",
    summary="Synthesize text to speech",
    dependencies=[Depends(standard_rate_limit)],
)
async def synthesize_speech(
    data: SynthesizeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Synthesize text to audio using the user's configured TTS provider."""
    try:
        tts = await get_tts_provider(db, current_user.id)
        audio_bytes = await tts.synthesize(data.text, data.voice_id)
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except ValueError as e:
        logger.error("TTS synthesis failed for user %s: %s", current_user.id, e)
        raise HTTPException(
            status_code=500,
            detail="Sprachsynthese fehlgeschlagen. Bitte prüfe deinen API Key.",
        ) from e
    except Exception as e:
        logger.error("Unexpected TTS error for user %s: %s", current_user.id, e)
        raise HTTPException(
            status_code=500,
            detail="Sprachsynthese fehlgeschlagen.",
        ) from e
