import os
import json
import re
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


class NLPService:
    def __init__(self):
        # Sarvam AI's OpenAI-compatible endpoint
        api_key = os.getenv("SARVAM_API_KEY")
        base_url = "https://api.sarvam.ai/v1"
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def analyze_transcript(self, transcript: str) -> dict:
        """
        Analyzes the transcript for SOP validation, summarization, and analytics.
        Enforces complianceScore = true_count / 5 deterministically after LLM response.
        """

        prompt = f"""
You are a call center compliance analyst. Analyze the following transcript which may be in Hindi (Hinglish), Tamil (Tanglish), or English.

Transcript:
\"\"\"{transcript}\"\"\"

Perform the following analysis:

1. SUMMARY: A concise summary (2-4 sentences) capturing the core purpose and outcome of the call.

2. SOP VALIDATION — evaluate each criterion as true or false:
   - greeting: Did the agent greet the customer at the start?
   - identification: Did the agent confirm or ask for the customer's name?
   - problemStatement: Was the reason for the call clearly stated?
   - solutionOffering: Did the agent propose a solution, plan, or next step?
   - closing: Did the agent close the call professionally?

3. COMPLIANCE SCORE: Count of 'true' values divided by 5. Must be exact.
   Examples: 5 true → 1.0 | 4 true → 0.8 | 3 true → 0.6 | 2 true → 0.4 | 1 true → 0.2 | 0 true → 0.0

4. ADHERENCE STATUS: Exactly "FOLLOWED" if complianceScore is 1.0, otherwise exactly "NOT_FOLLOWED".

5. EXPLANATION: One or two sentences explaining the compliance result.

6. ANALYTICS:
   - paymentPreference: Must be exactly one of: "EMI", "FULL_PAYMENT", "PARTIAL_PAYMENT", "DOWN_PAYMENT". Default to "FULL_PAYMENT" if unclear.
   - rejectionReason: Must be exactly one of: "HIGH_INTEREST", "BUDGET_CONSTRAINTS", "ALREADY_PAID", "NOT_INTERESTED", "NONE". Use "NONE" if payment was completed or intent was positive.
   - sentiment: Must be exactly one of: "Positive", "Negative", "Neutral".

7. KEYWORDS: List of 5-10 keywords that are directly present in the transcript or summary. No invented words.

Respond ONLY with a valid JSON object. No markdown, no code fences, no explanation outside the JSON.

{{
    "summary": "...",
    "sop_validation": {{
        "greeting": true,
        "identification": false,
        "problemStatement": true,
        "solutionOffering": true,
        "closing": true,
        "complianceScore": 0.8,
        "adherenceStatus": "NOT_FOLLOWED",
        "explanation": "..."
    }},
    "analytics": {{
        "paymentPreference": "EMI",
        "rejectionReason": "NONE",
        "sentiment": "Positive"
    }},
    "keywords": ["keyword1", "keyword2", "keyword3"]
}}
"""

        try:
            response = self.client.chat.completions.create(
                model="sarvam-105b",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional call center compliance auditor. "
                            "Respond ONLY with valid JSON. No markdown, no code fences, "
                            "no text outside the JSON object."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            )

            content = response.choices[0].message.content.strip()

            # Strip markdown code fences — handles ```json, ```JSON, plain ```
            content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.IGNORECASE)
            content = re.sub(r"\s*```$", "", content, flags=re.IGNORECASE)
            content = content.strip()

            result_json = json.loads(content)

            # ── Enforce complianceScore deterministically (don't trust LLM arithmetic)
            sop = result_json.get("sop_validation", {})
            sop_keys = ["greeting", "identification", "problemStatement", "solutionOffering", "closing"]
            true_count = sum(1 for k in sop_keys if sop.get(k) is True)
            correct_score = round(true_count / 5, 1)
            sop["complianceScore"] = correct_score
            sop["adherenceStatus"] = "FOLLOWED" if correct_score == 1.0 else "NOT_FOLLOWED"
            result_json["sop_validation"] = sop

            # ── Ensure keywords is always a list
            if not isinstance(result_json.get("keywords"), list):
                result_json["keywords"] = []

            return result_json

        except json.JSONDecodeError as je:
            print(f"[ERROR] NLP JSON parse failed: {je}. Raw: {content[:500]}")
            raise RuntimeError(f"NLP returned invalid JSON: {je}")
        except Exception as e:
            print(f"[ERROR] NLP analysis failed: {e}")
            raise RuntimeError(f"NLP Analysis failed: {e}")
