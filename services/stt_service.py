import os
import requests
import subprocess
import math
from dotenv import load_dotenv

load_dotenv()

class STTService:
    def __init__(self):
        self.api_key = os.getenv("SARVAM_API_KEY")
        self.url = "https://api.sarvam.ai/speech-to-text-translate"
    
    def get_duration(self, audio_path: str) -> float:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        try:
            return float(result.stdout.strip())
        except ValueError:
            print(f"DEBUG: ffprobe failed to get duration. Output: '{result.stdout}' for path: {audio_path}")
            return 0.0

    def split_audio(self, audio_path: str, chunk_duration=28) -> list:
        duration = self.get_duration(audio_path)
        print(f"DEBUG: Original audio duration: {duration}s")
        if duration <= chunk_duration:
            print("DEBUG: Duration is less than chunk duration, skipping split.")
            return [audio_path]
            
        base, ext = os.path.splitext(audio_path)
        chunks = []
        num_chunks = math.ceil(duration / chunk_duration)
        
        for i in range(num_chunks):
            start_time = i * chunk_duration
            chunk_path = f"{base}_chunk_{i}{ext}"
            subprocess.run([
                "ffmpeg", "-y", "-i", audio_path,
                "-ss", str(start_time),
                "-t", str(chunk_duration),
                chunk_path
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            chunks.append(chunk_path)
        return chunks

    def transcribe(self, audio_path: str) -> dict:
        """Transcribes audio using Sarvam AI's STT API with chunking support."""
        if not self.api_key:
            raise ValueError("SARVAM_API_KEY not found in environment.")

        try:
            chunks = self.split_audio(audio_path, chunk_duration=28)
            full_transcript = []
            detected_language = "Multilingual (Detect)"
            
            for chunk_path in chunks:
                chunk_dur = self.get_duration(chunk_path)
                print(f"Processing chunk: {chunk_path} (Duration: {chunk_dur}s)")
                
                with open(chunk_path, "rb") as audio_file:
                    files = {
                        "file": (os.path.basename(chunk_path), audio_file, "audio/mpeg")
                    }
                    data = {} # speech-to-text-translate uses default saaras:v3 automatically
                    headers = {
                        "api-subscription-key": self.api_key
                    }
                    
                    response = requests.post(self.url, headers=headers, files=files, data=data)
                    
                    if response.status_code != 200:
                        print(f"Sarvam STT Error: {response.status_code} - {response.text}")
                    
                    response.raise_for_status()
                    result = response.json()
                    
                    if "language_code" in result:
                        detected_language = result["language_code"]
                    if "transcript" in result:
                        full_transcript.append(result["transcript"])
                        
                # Cleanup if this is a temporary chunk
                if chunk_path != audio_path and os.path.exists(chunk_path):
                    os.remove(chunk_path)
            
            return {
                "language": detected_language,
                "transcription": " ".join(full_transcript)
            }
            
        except Exception as e:
            print(f"Error in Sarvam STT transcription: {e}")
            raise RuntimeError(f"Transcription failed: {e}")
