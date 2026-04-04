import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class NLPService:
    def __init__(self):
        # Sarvam API is OpenAI-compatible
        api_key = os.getenv("SARVAM_API_KEY")
        base_url = "https://api.sarvam.ai/v1"
        self.client = OpenAI(api_key=api_key, base_url=base_url)
    
    def analyze_transcript(self, transcript: str) -> dict:
        """Analyzes the transcript for SOP validation, summarization, and analytics using Sarvam AI."""
        
        prompt = f"""
        You are a call center compliance analyst. Analyze the following transcript for a call that may include Hindi (Hinglish), Tamil (Tanglish), and English.
        
        Transcript: "{transcript}"
        
        Tasks:
        1. Summarize: Provide a brief summary of the conversation.
        2. SOP Validation: Evaluate the following 5 criteria as true/false:
           - Greeting: Did the agent greet the customer?
           - Identification: Did the agent identify the name of the customer?
           - Problem Statement: Was the reason for the call clearly stated?
           - Solution Offering: Did the agent offer a solution or plan?
           - Closing: Was the call closed with a professional greeting?
        3. Compliance Score: Calculate a float score (0.0 to 1.0). Each 'true' in the 5 criteria is worth 0.2.
        4. Adherence Status: Must be exactly one of: "FOLLOWED" (if score is 1.0) or "NOT_FOLLOWED" (if score < 1.0).
        5. Explanation: Provide a brief reasoning for the SOP score.
        6. Analytics:
           - Payment Preference: Categorize into exactly one of: "EMI", "FULL_PAYMENT", "PARTIAL_PAYMENT", "DOWN_PAYMENT". Do not output anything else. If unclear, assume "FULL_PAYMENT".
           - Rejection Reason: Categorize into exactly one of: "HIGH_INTEREST", "BUDGET_CONSTRAINTS", "ALREADY_PAID", "NOT_INTERESTED", "NONE".
           - Sentiment: "Positive", "Negative", or "Neutral".
        7. Keywords: Extract 5-10 main keywords from the transcript and summary.
        
        Output format (JSON):
        {{
            "summary": "...",
            "sop_validation": {{
                "greeting": true/false,
                "identification": true/false,
                "problemStatement": true/false,
                "solutionOffering": true/false,
                "closing": true/false,
                "complianceScore": 0.0,
                "adherenceStatus": "...",
                "explanation": "..."
            }},
            "analytics": {{
                "paymentPreference": "...",
                "rejectionReason": "...",
                "sentiment": "..."
            }},
            "keywords": ["...", "..."]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="sarvam-105b", # Using Sarvam's powerful 105B model
                messages=[
                    {"role": "system", "content": "You are a professional auditor for call center compliance. Respond only in JSON format."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extract content as JSON
            content = response.choices[0].message.content
            # Cleanup potential markdown code blocks if the model includes them
            if content.startswith("```"):
                content = content.split("```json")[-1].split("```")[0].strip()
            
            result_json = json.loads(content)
            return result_json
        except Exception as e:
            print(f"Error in Sarvam NLP analysis: {e}")
            raise RuntimeError(f"NLP Analysis failed: {e}")
