from models.core import PaymentEvent

def diagnose_event(event: PaymentEvent) -> dict:
    """
    Diagnose the root cause of the payment event deterministically.
    Supported root causes: TRANSIENT, HARD_DECLINE, ABANDONMENT, MANDATE_ISSUE, NON_PAYMENT, SUCCESS
    """
    if event.event_type == "payment.succeeded":
        return {
            "root_cause": "SUCCESS",
            "confidence": 1.0,
            "reasoning": "Payment was successful."
        }
        
    if event.event_type == "checkout.abandoned":
        return {
            "root_cause": "ABANDONMENT",
            "confidence": 1.0,
            "reasoning": "Checkout ended without payment attempt."
        }
        
    error_code = event.error_code or ""
    method = ""
    if event.payload.get("payment") and event.payload["payment"].get("entity"):
        method = event.payload["payment"]["entity"].get("method", "")
        
    # TRANSIENT errors
    transient_codes = ["issuer_down", "timeout", "network_error", "BAD_REQUEST_ERROR", "GATEWAY_ERROR"]
    if any(code in error_code for code in transient_codes):
        return {
            "root_cause": "TRANSIENT",
            "confidence": 0.9,
            "reasoning": f"Error code '{error_code}' indicates a temporary issue."
        }
        
    # HARD_DECLINE errors
    hard_decline_codes = ["card_declined", "insufficient_funds", "expired_card", "invalid_card"]
    if any(code in error_code for code in hard_decline_codes):
        return {
            "root_cause": "HARD_DECLINE",
            "confidence": 0.9,
            "reasoning": f"Error code '{error_code}' indicates a hard decline."
        }
        
    # MANDATE_ISSUE
    if event.event_type == "subscription.charge.failed" and method in ["upi", "nach", "card", "emandate"]:
        if "mandate" in error_code.lower() or "auth" in error_code.lower():
            return {
                "root_cause": "MANDATE_ISSUE",
                "confidence": 0.85,
                "reasoning": "Subscription charge failed likely due to mandate issues."
            }
            
    # NON_PAYMENT (fallback for failed subscriptions without clear cause)
    if event.event_type == "subscription.charge.failed":
        return {
            "root_cause": "NON_PAYMENT",
            "confidence": 0.7,
            "reasoning": "Subscription charge failed with unclear cause."
        }
        
    # Default fallback
    return {
        "root_cause": "HARD_DECLINE",
        "confidence": 0.5,
        "reasoning": "Fallback classification for unknown error."
    }
