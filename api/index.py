import os
import uuid
import base64
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Header, Request
from pydantic import BaseModel, Field
from services.stt_service import STTService
from services.nlp_service import NLPService
# from services.vector_service import VectorService
from utils.audio_utils import decode_audio_base64, cleanup_file
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Call Center Compliance API")

# Initialize services
stt_service = STTService()
nlp_service = NLPService()
# vector_service = VectorService()

# Mock API Key for validation as per rubric
SECRET_API_KEY = os.getenv("API_KEY", "GUVI_HACKATHON_DEMO_KEY")

class CallRequest(BaseModel):
    # Allow extra fields so we can inspect exactly what the runner is sending
    class Config:
        extra = "allow"

    @property
    def get_audio(self) -> str:
        # Support both Pydantic v1 and v2 for getting all fields
        data_dict = self.dict() if hasattr(self, "dict") else self.model_dump()
        
        # Check common keys
        val = data_dict.get("audio") or data_dict.get("audio_base64") or data_dict.get("audio_file")
        
        if not val:
            keys = list(data_dict.keys())
            raise ValueError(f"Debug: Audio missing. Received JSON keys: {keys}")
        return val

@app.get("/")
def read_root():
    return {"message": "Call Center Compliance API is running."}

@app.post("/api/call-analytics")
async def call_analytics(request: CallRequest, x_api_key: Optional[str] = Header(None)):
    # 1. API Key Validation
    if x_api_key != SECRET_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key.")
    
    # 2. Decode Audio
    audio_path = None
    try:
        audio_path = decode_audio_base64(request.get_audio)
        
        # 3. Speech-to-Text
        stt_result = stt_service.transcribe(audio_path)
        transcript = stt_result.get("transcription", "")
        language = stt_result.get("language", "Unknown")
        
        if not transcript:
            return {
                "status": "error",
                "message": "Transcription failed or returned empty text."
            }
        
        # 4. NLP Analysis (SOP Validation, Summarization, Analytics)
        analysis_result = nlp_service.analyze_transcript(transcript)
        
        # vector_service.add_transcript(transcript, metadata=analysis_result["analytics"])
        
        # 6. Final Response Construction
        return {
            "status": "success",
            "language": language,
            "transcript": transcript,
            "summary": analysis_result.get("summary", ""),
            "sop_validation": analysis_result.get("sop_validation", {}),
            "analytics": analysis_result.get("analytics", {}),
            "keywords": analysis_result.get("keywords", [])
        }
        
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Server Error: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error during processing.")
    finally:
        # Cleanup
        if audio_path:
            cleanup_file(audio_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
