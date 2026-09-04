from models.core import PaymentEvent
import logging

logger = logging.getLogger(__name__)

# Heuristic base probabilities based on root cause
HEURISTIC_PROBABILITIES = {
    "TRANSIENT": 0.85,
    "HARD_DECLINE": 0.20,
    "ABANDONMENT": 0.15,
    "MANDATE_ISSUE": 0.40,
    "NON_PAYMENT": 0.10,
    "SUCCESS": 0.0
}

def calculate_recovery_score(event: PaymentEvent, diagnosis: dict, policy: dict) -> dict:
    """
    Calculates expected recovery value and priority score using deterministic heuristics.
    Structured to allow future replacement with a real ML model.
    """
    root_cause = diagnosis.get("root_cause", "NON_PAYMENT")
    
    # 1. Base recovery probability
    base_probability = HEURISTIC_PROBABILITIES.get(root_cause, 0.1)
    
    # 2. Adjustments (e.g. based on attempts)
    # If the policy allows 3 attempts and this is the 3rd, probability drops.
    # For now, stick to base probability for simplicity.
    recovery_probability = base_probability
    
    # 3. Expected Value
    amount = 0.0
    if event.payload.get("payment"):
        amount = event.payload["payment"].get("entity", {}).get("amount", 0) / 100.0
        
    expected_recovery_value = amount * recovery_probability
    
    # 4. Priority Score (Normalized 0-100 heuristic)
    # Example heuristic: EV normalized by an arbitrary max expected transaction (e.g., 10,000 INR).
    # Cap at 100.
    priority_score = min(100.0, (expected_recovery_value / 10000.0) * 100.0)
    
    score_data = {
        "recovery_probability": round(recovery_probability, 2),
        "expected_recovery_value": round(expected_recovery_value, 2),
        "priority_score": round(priority_score, 2),
        "amount": amount
    }
    
    logger.info(f"Calculated Score for {event.id}: {score_data}")
    return score_data
