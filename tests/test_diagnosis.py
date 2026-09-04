from engines.diagnosis import diagnose_event
from models.core import PaymentEvent

def test_diagnose_transient():
    event = PaymentEvent(
        event_type="payment.failed",
        error_code="issuer_down",
        payload={"payment": {"entity": {"method": "upi"}}}
    )
    result = diagnose_event(event)
    assert result["root_cause"] == "TRANSIENT"

def test_diagnose_hard_decline():
    event = PaymentEvent(
        event_type="payment.failed",
        error_code="insufficient_funds",
        payload={"payment": {"entity": {"method": "card"}}}
    )
    result = diagnose_event(event)
    assert result["root_cause"] == "HARD_DECLINE"

def test_diagnose_abandonment():
    event = PaymentEvent(
        event_type="checkout.abandoned",
        error_code=None,
        payload={}
    )
    result = diagnose_event(event)
    assert result["root_cause"] == "ABANDONMENT"
