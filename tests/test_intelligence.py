from engines.intelligence import calculate_recovery_score
from models.core import PaymentEvent

def test_intelligence_scoring_transient():
    event = PaymentEvent(id="ev_int_1", payload={"payment": {"entity": {"amount": 500000}}}) # 5000 INR
    diagnosis = {"root_cause": "TRANSIENT"}
    policy = {}
    
    score = calculate_recovery_score(event, diagnosis, policy)
    
    assert score["recovery_probability"] == 0.85
    assert score["amount"] == 5000.0
    assert score["expected_recovery_value"] == 5000.0 * 0.85
    assert score["priority_score"] == min(100.0, ((5000.0 * 0.85) / 10000.0) * 100.0)

def test_intelligence_scoring_hard_decline():
    event = PaymentEvent(id="ev_int_2", payload={"payment": {"entity": {"amount": 1000000}}}) # 10000 INR
    diagnosis = {"root_cause": "HARD_DECLINE"}
    policy = {}
    
    score = calculate_recovery_score(event, diagnosis, policy)
    
    assert score["recovery_probability"] == 0.20
    assert score["expected_recovery_value"] == 10000.0 * 0.20
