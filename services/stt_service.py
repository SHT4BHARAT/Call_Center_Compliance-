import os
import requests
from dotenv import load_dotenv

load_dotenv()

class STTService:
    def __init__(self):
        self.api_key = os.getenv("SARVAM_API_KEY")
        self.url = "https://api.sarvam.ai/speech-to-text"
    
    def transcribe(self, audio_path: str) -> dict:
        """Transcribes audio using Sarvam AI's STT API."""
        if not self.api_key:
            raise ValueError("SARVAM_API_KEY not found in environment.")

        try:
            with open(audio_path, "rb") as audio_file:
                files = {
                    "file": (os.path.basename(audio_path), audio_file, "audio/mpeg")
                }
                data = {
                    "model": "saaras:v3",
                    "mode": "codemix" # Specifically for Hinglish/Tanglish
                }
                headers = {
                    "api-subscription-key": self.api_key
                }
                
                response = requests.post(self.url, headers=headers, files=files, data=data)
                response.raise_for_status()
                
                result = response.json()
                
                return {
                    "language": result.get("language_code", "Multilingual (Detect)"),
                    "transcription": result.get("transcript", "")
                }
        except Exception as e:
            print(f"Error in Sarvam STT transcription: {e}")
            raise RuntimeError(f"Transcription failed: {e}")
