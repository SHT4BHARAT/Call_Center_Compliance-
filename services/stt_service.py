import os
import requests
from dotenv import load_dotenv

load_dotenv()

class STTService:
    def __init__(self):
        self.api_key = os.getenv("SARVAM_API_KEY")
        self.url = "https://api.sarvam.ai/speech-to-text-translate"
    
    def transcribe(self, audio_path: str) -> dict:
        """Transcribes audio using Sarvam AI's STT API.
        
        Note: Manual chunking via ffmpeg is removed for Vercel compatibility.
        Direct upload is used for files up to 30 seconds (REST) or larger (Batch).
        """
        if not self.api_key:
            raise ValueError("SARVAM_API_KEY not found in environment.")

        try:
            with open(audio_path, "rb") as audio_file:
                files = {
                    "file": (os.path.basename(audio_path), audio_file, "audio/mpeg")
                }
                data = {
                    "model": "saaras:v1" # Standard model for fast STT
                }
                headers = {
                    "api-subscription-key": self.api_key
                }
                
                print(f"Sending audio file directly to Sarvam: {audio_path}")
                response = requests.post(self.url, headers=headers, files=files, data=data)
                
                if response.status_code != 200:
                    print(f"Sarvam STT Error: {response.status_code} - {response.text}")
                
                response.raise_for_status()
                result = response.json()
                
                # The response from Sarvam AI's speech-to-text-translate
                # typically contains 'transcript' and 'language_code'.
                return {
                    "language": result.get("language_code", "Unknown"),
                    "transcription": result.get("transcript", "")
                }
                
        except Exception as e:
            print(f"Error in Sarvam STT transcription: {e}")
            raise RuntimeError(f"Transcription failed: {e}")
