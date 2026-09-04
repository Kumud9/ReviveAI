import json

def build_agent_context(payment_data: dict, recovery_probability: float, expected_value: float, available_actions: list) -> str:
    """
    Builds a secure, cleanly separated context string for the LLM.
    Ensures clear separation of facts, model outputs, and allowed actions.
    """
    
    # We strictly separate facts from AI models
    facts = {
        "amount": payment_data.get("amount", 0.0),
        "currency": payment_data.get("currency", "INR"),
        "payment_method": payment_data.get("payment_method", "unknown"),
        "error_code": payment_data.get("error_code", "unknown"),
        "root_cause_diagnosis": payment_data.get("root_cause_diagnosis", "unknown"),
        "historical_success_rate": payment_data.get("historical_success_rate", 0.0),
        "historical_recovery_rate": payment_data.get("historical_recovery_rate", 0.0),
        "previous_failure_count": payment_data.get("previous_failure_count", 0),
        "subscription_status": payment_data.get("subscription_status", "NONE"),
        "customer_notes": payment_data.get("customer_notes", "") # Untrusted customer data
    }
    
    model_outputs = {
        "ml_recovery_probability": round(recovery_probability, 4),
        "expected_recovery_value": round(expected_value, 2)
    }
    
    context_block = {
        "FACTS": facts,
        "MODEL_OUTPUTS": model_outputs,
        "AVAILABLE_ACTIONS": available_actions
    }
    
    # Format as JSON string for unambiguous boundaries
    return json.dumps(context_block, indent=2)
