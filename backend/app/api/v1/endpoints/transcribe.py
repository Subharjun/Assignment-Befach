from fastapi import APIRouter, HTTPException, UploadFile, File
import httpx

from app.core.config import get_settings

router = APIRouter(prefix="/transcribe", tags=["transcribe"])

GROQ_BASE = "https://api.groq.com/openai/v1"


@router.post("")
async def transcribe_audio(file: UploadFile = File(...)):
    settings = get_settings()
    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="Transcription not configured (GROQ_API_KEY missing)")

    audio_bytes = await file.read()
    filename = file.filename or "audio.webm"
    content_type = file.content_type or "audio/webm"

    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            f"{GROQ_BASE}/audio/transcriptions",
            headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            files={"file": (filename, audio_bytes, content_type)},
            data={"model": "whisper-large-v3", "language": "en"},
        )
        r.raise_for_status()

    return {"text": r.json().get("text", "")}
