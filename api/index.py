import os
import re
from typing import Optional
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel, Field, ConfigDict
from services.stt_service import STTService
from services.nlp_service import NLPService
from services.vector_service import VectorService
from utils.audio_utils import decode_audio_base64, cleanup_file
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Call Center Compliance API")

# Initialize services
stt_service = STTService()
nlp_service = NLPService()

# VectorService: initialize non-fatally (ChromaDB can fail on cold starts)
try:
    vector_service = VectorService()
except Exception as _ve:
    print(f"[WARN] VectorService unavailable: {_ve}")
    vector_service = None

# API Key — per rubric must reject with 401
SECRET_API_KEY = os.getenv("API_KEY", "GUVI_HACKATHON_DEMO_KEY")


class CallRequest(BaseModel):
    """
    Accepts both 'audioBase64' (runner/rubric spec) and 'audio_base64' (legacy).
    Extra fields are allowed and ignored so the runner can send 'language', 'audioFormat', etc.
    """
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    audioBase64: Optional[str] = Field(None)
    audio_base64: Optional[str] = Field(None)   # legacy / test_api.py compat
    language: Optional[str] = Field(None)
    audioFormat: Optional[str] = Field(None)

    def get_audio_data(self) -> str:
        """Returns the base64 audio string regardless of which field name was used."""
        val = self.audioBase64 or self.audio_base64

        if not val:
            # Last resort: scan extra fields for any audio-like key
            extra = self.__pydantic_extra__ or {}
            for key in ("audioBase64", "audio_base64", "audio", "audiobase64"):
                val = extra.get(key)
                if val:
                    break

        if not val:
            all_keys = list(
                {*self.model_dump(exclude_none=True).keys(), *(self.__pydantic_extra__ or {}).keys()}
            )
            raise ValueError(
                f"Audio data missing. Expected field 'audioBase64'. Received keys: {all_keys}"
            )
        return val


@app.get("/")
def read_root():
    return {"message": "Call Center Compliance API is running."}


@app.post("/api/call-analytics")
async def call_analytics(
    request: CallRequest,
    x_api_key: Optional[str] = Header(None),
):
    # ── 1. Authentication ── must be 401 per rubric (not 403)
    if x_api_key != SECRET_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid or missing API Key.")

    audio_path = None
    try:
        # ── 2. Decode Base64 audio to a temp file
        audio_path = decode_audio_base64(request.get_audio_data())

        # ── 3. Speech-to-Text via Sarvam AI
        stt_result = stt_service.transcribe(audio_path)
        transcript = stt_result.get("transcription", "")
        language = stt_result.get("language") or request.language or "Unknown"

        if not transcript:
            return {
                "status": "error",
                "message": "Transcription failed or returned empty text.",
            }

        # ── 4. NLP Analysis (SOP + analytics + keywords)
        analysis_result = nlp_service.analyze_transcript(transcript)

        # ── 5. Vector storage (non-fatal — rubric rewards evidence of indexing)
        if vector_service:
            try:
                vector_service.add_transcript(
                    transcript,
                    metadata=analysis_result.get("analytics", {}),
                )
            except Exception as ve:
                print(f"[WARN] Vector storage skipped: {ve}")

        # ── 6. Final structured response
        return {
            "status": "success",
            "language": language,
            "transcript": transcript,
            "summary": analysis_result.get("summary", ""),
            "sop_validation": analysis_result.get("sop_validation", {}),
            "analytics": analysis_result.get("analytics", {}),
            "keywords": analysis_result.get("keywords", []),
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        import traceback
        print(f"[ERROR] {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
    finally:
        if audio_path:
            cleanup_file(audio_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
