# Call Center Compliance API

## Description

A production-ready AI-powered API that analyzes call center recordings for compliance, built for the GUVI Hackathon 2026 (Track 3). The system accepts Base64-encoded MP3 audio, performs multi-stage AI analysis, and returns structured JSON containing transcription, SOP compliance scores, payment intent, and sentiment analytics.

**Strategy:** The pipeline uses Sarvam AI's Speech-to-Text API for accurate Hinglish/Tanglish transcription, followed by Sarvam's LLM (OpenAI-compatible endpoint) for NLP analysis. Compliance scores are enforced deterministically server-side to guarantee rubric accuracy regardless of LLM arithmetic drift.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI (Python) |
| Runtime | Uvicorn (ASGI) |
| Speech-to-Text | Sarvam AI (`saaras:v1`) — Hinglish & Tanglish support |
| NLP / LLM | Sarvam AI (`sarvam-105b`) via OpenAI-compatible API |
| Vector Storage | ChromaDB (persistent, `/tmp/chroma` on serverless) |
| Deployment | Vercel Serverless Functions |
| Validation | Pydantic v2 |

---

## API Reference

### `POST /api/call-analytics`

**Headers:**
```
Content-Type: application/json
x-api-key: YOUR_SECRET_API_KEY
```

**Request Body:**
```json
{
  "language": "Tamil",
  "audioFormat": "mp3",
  "audioBase64": "<base64-encoded-mp3>"
}
```

**Success Response (200):**
```json
{
  "status": "success",
  "language": "Tamil",
  "transcript": "...",
  "summary": "...",
  "sop_validation": {
    "greeting": true,
    "identification": false,
    "problemStatement": true,
    "solutionOffering": true,
    "closing": true,
    "complianceScore": 0.8,
    "adherenceStatus": "NOT_FOLLOWED",
    "explanation": "..."
  },
  "analytics": {
    "paymentPreference": "EMI",
    "rejectionReason": "NONE",
    "sentiment": "Positive"
  },
  "keywords": ["keyword1", "keyword2"]
}
```

**Error Responses:**
- `401 Unauthorized` — Missing or invalid `x-api-key`
- `400 Bad Request` — Missing or undecodable audio data
- `500 Internal Server Error` — STT or NLP pipeline failure

---

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set environment variables
```bash
cp .env.example .env
# Edit .env and add your keys
```

Required variables:
```
SARVAM_API_KEY=your_sarvam_api_key_here
API_KEY=GUVI_HACKATHON_DEMO_KEY
```

### 4. Run locally
```bash
uvicorn api.index:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Test the API
```bash
python test_api.py
```

---

## Approach

1. **Audio Decoding** — Base64 string decoded to a temp `.mp3` file using `audio_utils.py`
2. **Speech-to-Text** — Audio sent to Sarvam AI's `speech-to-text-translate` endpoint, which natively supports Hinglish and Tanglish
3. **NLP Analysis** — Transcript analyzed by Sarvam's 105B LLM via an OpenAI-compatible endpoint with a structured compliance prompt
4. **Deterministic Scoring** — `complianceScore` is computed server-side by counting true SOP steps (not trusted from LLM) to ensure accuracy
5. **Vector Indexing** — Transcripts indexed into ChromaDB for semantic search evidence
6. **Structured Response** — All fields returned strictly matching the rubric schema

---

## Project Structure

```
.
├── api/
│   └── index.py          # FastAPI app, routing, auth
├── services/
│   ├── stt_service.py    # Sarvam AI Speech-to-Text
│   ├── nlp_service.py    # Sarvam AI LLM NLP analysis
│   └── vector_service.py # ChromaDB transcript indexing
├── utils/
│   └── audio_utils.py    # Base64 decode, temp file cleanup
├── scripts/
│   └── start_tunnel.ps1  # Local Cloudflare tunnel helper
├── test_api.py           # Local end-to-end test runner
├── requirements.txt      # Python dependencies
├── vercel.json           # Vercel routing config
└── .env.example          # Environment variable template
```
