import base64
import requests
import json
import os

# Configuration
API_URL = "http://localhost:8000/api/call-analytics"
API_KEY = "GUVI_HACKATHON_DEMO_KEY"
SAMPLE_AUDIO_PATH = "sample.mp3"

def test_api():
    if not os.path.exists(SAMPLE_AUDIO_PATH):
        print(f"Error: {SAMPLE_AUDIO_PATH} not found. Please download it first.")
        return

    # 1. Read and encode audio
    with open(SAMPLE_AUDIO_PATH, "rb") as f:
        audio_content = f.read()
        audio_base64 = base64.b64encode(audio_content).decode("utf-8")

    # 2. Prepare payload
    payload = {
        "audio_base64": audio_base64
    }
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }

    # 3. Call API
    print(f"Sending request to {API_URL}...")
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            print("Success! Response JSON:")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_api()
