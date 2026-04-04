import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class NLPService:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    def analyze_transcript(self, transcript: str) -> dict:
        """Analyzes the transcript for SOP validation, summarization, and analytics."""
        
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
        3. Compliance Score: Calculate a float score (0.0 to 1.0) based on adherence.
        4. Adherence Status: Must be one of: "FOLLOWED", "PARTIALLY_FOLLOWED", or "NOT_FOLLOWED".
        5. Explanation: Provide a brief reasoning for the SOP score.
        6. Analytics:
           - Payment Preference: Categorize into exactly one of: "EMI", "FULL_PAYMENT", "PARTIAL_PAYMENT", "DOWN_PAYMENT", "NONE".
           - Rejection Reason: Categorize into exactly one of: "HIGH_INTEREST", "BUDGET_CONSTRAINTS", "ALREADY_PAID", "NOT_INTERESTED", "NONE".
           - Sentiment: "Positive", "Negative", or "Neutral".
        7. Keywords: Extract 3-5 technical keywords (e.g., Catia, AutoCAD).
        
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
                model="gpt-4o", # Using a strong reasoning model for accuracy
                messages=[
                    {"role": "system", "content": "You are a professional auditor for call center compliance."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            # Extract content as JSON
            result_json = json.loads(response.choices[0].message.content)
            return result_json
        except Exception as e:
            print(f"Error in NLP analysis: {e}")
            raise RuntimeError(f"NLP Analysis failed: {e}")
