from engines.guardrails import evaluate_guardrails
from models.core import PaymentEvent, Payment, Customer, RecoveryAttempt
import pytest
from datetime import datetime, timedelta
import uuid

def test_guardrail_already_paid(db_session):
    event = PaymentEvent(id="ev_1", payment_id="pay_1")
    payment = Payment(id="pay_1", status="captured")
    db_session.add(event)
    db_session.add(payment)
    db_session.commit()
    
    allowed, reason = evaluate_guardrails(event, "retry_payment", {"actions": ["retry_payment"]}, db_session)
    assert not allowed
    assert reason == "ALREADY_PAID"

def test_guardrail_dnd(db_session):
    customer = Customer(id="cust_1", dnd=True)
    event = PaymentEvent(id="ev_2", customer_id="cust_1")
    db_session.add(customer)
    db_session.add(event)
    db_session.commit()
    
    allowed, reason = evaluate_guardrails(event, "retry_payment", {"actions": ["retry_payment"]}, db_session)
    assert not allowed
    assert reason == "CUSTOMER_DND"

def test_guardrail_max_attempts(db_session):
    event = PaymentEvent(id="ev_3")
    db_session.add(event)
    db_session.commit()
    
    # 2 previous attempts
    db_session.add(RecoveryAttempt(id=str(uuid.uuid4()), event_id=event.id, created_at=datetime.utcnow() - timedelta(hours=2)))
    db_session.add(RecoveryAttempt(id=str(uuid.uuid4()), event_id=event.id, created_at=datetime.utcnow() - timedelta(hours=1)))
    db_session.commit()
    
    policy = {"actions": ["retry_payment"], "max_attempts": 2}
    allowed, reason = evaluate_guardrails(event, "retry_payment", policy, db_session)
    
    assert not allowed
    assert reason == "MAX_ATTEMPTS_REACHED"

def test_guardrail_cooldown(db_session):
    event = PaymentEvent(id="ev_4")
    db_session.add(event)
    db_session.commit()
    
    # 1 previous attempt 30 minutes ago
    db_session.add(RecoveryAttempt(id=str(uuid.uuid4()), event_id=event.id, created_at=datetime.utcnow() - timedelta(minutes=30)))
    db_session.commit()
    
    policy = {"actions": ["retry_payment"], "max_attempts": 3, "cooldown_hours": [1, 6, 24]}
    allowed, reason = evaluate_guardrails(event, "retry_payment", policy, db_session)
    
    assert not allowed
    assert reason == "COOLDOWN_NOT_ELAPSED"
