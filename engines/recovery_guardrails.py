from typing import Dict, Any

class RecoveryGuardrails:
    """
    Deterministic Guardrails.
    The final fail-closed gatekeeper before actual execution.
    """
    AVAILABLE_ACTIONS = {
        "retry_payment", 
        "payment_link", 
        "reminder", 
        "subscription_recovery", 
        "human_escalation",
        "no_action"
    }

    def verify(self, policy_decision: Dict[str, Any], event_data: Dict[str, Any], attempt_history: list) -> Dict[str, Any]:
        """
        Returns a structured guardrail decision:
        {
          "status": "ALLOW" | "DENY" | "HUMAN_REVIEW",
          "reason": str,
          "action": str
        }
        """
        action = policy_decision.get("action")
        
        # 1. Action must be in explicitly allowed set
        if action not in self.AVAILABLE_ACTIONS:
            return self._deny(action, f"Action '{action}' is not in the explicitly permitted AVAILABLE_ACTIONS list.")
            
        # 2. Check if Policy requires human review
        if policy_decision.get("requires_human_review"):
            return self._human_review(action, policy_decision.get("reason", "Policy required human review."))
            
        # 3. Check if Policy denied the action
        if not policy_decision.get("allowed"):
            return self._deny(action, policy_decision.get("reason", "Policy denied the action."))
            
        # 4. Idempotency / duplicate check within recent time frame 
        # (Already partially handled by policy cooldown, but guardrail enforces no duplicate action in progress)
        for attempt in attempt_history:
            if attempt.get("status") in ["IN_PROGRESS", "PENDING"]:
                return self._deny(action, f"An action ({attempt.get('action')}) is already in progress.")
                
        # 5. Missing mandatory data for execution
        # A retry requires an amount and a currency
        if action in ["retry_payment", "payment_link"]:
            if not event_data.get("amount") or not event_data.get("currency"):
                return self._deny(action, "Missing required fields: amount or currency for financial action.")
            if float(event_data.get("amount")) <= 0:
                return self._deny(action, "Amount must be strictly positive.")

        return self._allow(action, "All guardrail checks passed.")

    def _allow(self, action: str, reason: str) -> Dict[str, Any]:
        return {"status": "ALLOW", "reason": reason, "action": action}

    def _deny(self, action: str, reason: str) -> Dict[str, Any]:
        return {"status": "DENY", "reason": reason, "action": action}
        
    def _human_review(self, action: str, reason: str) -> Dict[str, Any]:
        return {"status": "HUMAN_REVIEW", "reason": reason, "action": action}
