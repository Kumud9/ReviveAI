import os
import json
import logging
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Abstracted LLM client that provides a standard interface for generating structured responses.
    """
    def __init__(self, api_key: str = None, model: str = None, base_url: str = None):
        self.api_key = api_key or os.environ.get("LLM_API_KEY")
        self.model = model or os.environ.get("LLM_MODEL", "gpt-4-turbo")
        self.base_url = base_url or os.environ.get("LLM_BASE_URL")
        
        self.client = None
        if self.api_key and OpenAI:
            try:
                kwargs = {"api_key": self.api_key}
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                self.client = OpenAI(**kwargs)
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                
    def is_configured(self) -> bool:
        return self.client is not None

    def generate_structured(self, system_prompt: str, user_prompt: str) -> dict:
        """
        Generates a structured JSON response from the LLM.
        """
        if not self.is_configured():
            logger.warning("LLM client not configured (missing API key or openai library). Returning safe mock.")
            return self._mock_response()
            
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error calling LLM: {e}")
            return self._safe_fallback()

    def _mock_response(self) -> dict:
        """
        A static mock response used when the LLM is not configured, primarily for tests/demo.
        """
        return {
            "decision": "human_escalation",
            "confidence": 0.5,
            "reason": "Fallback triggered due to unconfigured LLM client.",
            "priority": "high",
            "estimated_recovery_value": 0.0,
            "requires_human_review": True,
            "evidence": ["Mock response generated."]
        }
        
    def _safe_fallback(self) -> dict:
        """
        Safe fallback if the LLM crashes or returns invalid JSON.
        """
        return {
            "decision": "human_escalation",
            "confidence": 0.0,
            "reason": "System encountered an error calling the LLM.",
            "priority": "high",
            "estimated_recovery_value": 0.0,
            "requires_human_review": True,
            "evidence": ["Error fallback"]
        }
