"""
Gemini API client integration
Task 3.2: Gemini API Integration
"""
import google.generativeai as genai
from config import settings
from typing import Optional, Dict, Any
import json

# Configure Gemini
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)


class GeminiClient:
    """
    Wrapper for Gemini API calls
    """

    def __init__(self):
        self.model_name = "gemini-2.5-flash-lite"
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config={
                "temperature": 0.7,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
        )

    def generate_response(
        self,
        prompt: str,
        tools: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Generate response from Gemini

        Args:
            prompt: The full prompt including context and instructions
            tools: Optional list of tool definitions for function calling

        Returns:
            Dict with 'text' and optional 'function_calls'
        """
        try:
            # For MVP, we'll use text generation and parse JSON from response
            # In production, would use Gemini's function calling feature

            response = self.model.generate_content(prompt)

            return {
                "text": response.text,
                "function_calls": []  # Will be populated when we add function calling
            }

        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

    def parse_json_response(self, text: str) -> Optional[Dict]:
        """
        Try to extract JSON from response text
        """
        try:
            # Look for JSON in code blocks
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                json_str = text[start:end].strip()
                return json.loads(json_str)
            # Try parsing the whole text
            return json.loads(text)
        except:
            return None
