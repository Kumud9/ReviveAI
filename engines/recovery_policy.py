from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

class RecoveryPolicyEngine:
    """
    Deterministic Policy Engine.
    Evaluates ML predictions, LLM recommendations, and historical attempt data 
    to decide if an action is allowed, denied, or requires human review.
    """
    MAX_ATTEMPTS = 3
    COOLDOWN_HOURS = 1
    HIGH_VALUE_THRESHOLD = 100000.0
    LOW_CONFIDENCE_THRESHOLD = 0.6
    
    def __init__(self, db_session=None):
        self.db = db_session
        
    def evaluate(self, event_data: dict, ml_probability: float, llm_recommendation: dict, attempt_history: List[dict]) -> dict:
        """
        Returns a structured policy decision:
        {
          "allowed": bool,
          "action": str,
          "reason": str,
          "requires_human_review": bool
        }
        """
        llm_action = llm_recommendation.get("decision", "no_action")
        confidence = llm_recommendation.get("confidence", 0.0)
        
        # 1. Check if already recovered
        if event_data.get("status") == "captured":
            return self._deny("already_recovered", "Payment is already successfully captured.")
            
        # 2. Check exhausted attempts
        if len(attempt_history) >= self.MAX_ATTEMPTS:
            return self._deny("max_attempts_reached", f"Maximum of {self.MAX_ATTEMPTS} attempts reached.")
            
        # 3. Check cooldown
        if attempt_history:
            last_attempt_time = attempt_history[-1].get("created_at")
            if last_attempt_time:
                # Naive datetime comparison
                time_since_last = datetime.utcnow() - last_attempt_time
                if time_since_last < timedelta(hours=self.COOLDOWN_HOURS):
                    return self._deny("cooldown_active", f"Cooldown period of {self.COOLDOWN_HOURS} hours not satisfied.")
                    
        # 4. Check missing context
        amount = event_data.get("amount")
        if amount is None or event_data.get("currency") is None:
            return self._human_review(llm_action, "Invalid or missing context (amount/currency).")
            
        # 5. Check high-value threshold
        if float(amount) >= self.HIGH_VALUE_THRESHOLD:
            return self._human_review(llm_action, f"High-value amount ({amount}) exceeds threshold ({self.HIGH_VALUE_THRESHOLD}).")
            
        # 6. Check low confidence
        if confidence < self.LOW_CONFIDENCE_THRESHOLD:
            return self._human_review(llm_action, f"LLM confidence ({confidence}) is below threshold ({self.LOW_CONFIDENCE_THRESHOLD}).")
            
        # 7. Check if LLM explicitly asked for human escalation
        if llm_action == "human_escalation":
            return self._human_review(llm_action, "LLM recommended human escalation.")
            
        if llm_action == "no_action":
            return self._deny("no_action", "LLM recommended no action.")
            
        # If all checks pass, allow the action
        return {
            "allowed": True,
            "action": llm_action,
            "reason": "Policy passed all checks.",
            "requires_human_review": False
        }
        
    def _deny(self, action: str, reason: str) -> dict:
        return {
            "allowed": False,
            "action": action,
            "reason": reason,
            "requires_human_review": False
        }
        
    def _human_review(self, action: str, reason: str) -> dict:
        return {
            "allowed": False,
            "action": action,
            "reason": reason,
            "requires_human_review": True
        }
