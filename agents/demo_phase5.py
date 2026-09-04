import sys
import os
import json
import uuid
import pprint
from dotenv import load_dotenv

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.base import Base
from models.core import AuditLog, RecoveryOutcome, PaymentEvent
from ml.predict import predict_recovery_probability
from services.llm_client import LLMClient
from agents.recovery_agent import RecoveryAgent
from services.executor import RecoveryExecutor
from services.orchestrator import RecoveryOrchestrator
from services.outcome_tracker import OutcomeTracker
from schemas.events import RazorpayWebhookEvent

def run_phase5_demo():
    print("--- ReviveAI: Phase 5 Closed-Loop Recovery Demo ---")
    
    # 1. Setup DB
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # 2. Setup Services
    load_dotenv(override=True)
    class MockLLMClient:
        def is_configured(self): return True
        def generate_structured(self, *args, **kwargs):
            return {"decision": "payment_link", "confidence": 0.95, "reason": "Standard automated retry is safe.", "priority": "high", "estimated_recovery_value": 5000.0, "requires_human_review": False, "evidence": ["Mocked safe execution"]}
            
    client = MockLLMClient()
    llm_agent = RecoveryAgent(client)
    executor = RecoveryExecutor(db)
    tracker = OutcomeTracker(db)
    
    if executor.rzp_client:
        print("[INFO] Razorpay test credentials detected. WILL attempt execution.")
    else:
        print("[INFO] Razorpay test credentials NOT properly configured. Will NOT execute.")

    orchestrator = RecoveryOrchestrator(
        db=db,
        ml_predictor=predict_recovery_probability,
        llm_agent=llm_agent,
        executor=executor
    )
    
    # 3. Provide a mock payment opportunity
    event_id = str(uuid.uuid4())
    customer_id = f"cust_{uuid.uuid4()}"
    amount = 5000.0
    
    # Simulate DB insertion of initial event
    new_event = PaymentEvent(
        id=event_id,
        event_type="payment.failed",
        customer_id=customer_id,
        payment_id=f"pay_{uuid.uuid4()}",
        payload={}
    )
    db.add(new_event)
    db.commit()

    mock_opportunity = {
        "amount": amount,
        "currency": "INR",
        "payment_method": "upi",
        "transaction_hour": 14,
        "transaction_day": 2,
        "amount_relative_to_customer_average": 1.2,
        "error_code": "timeout",
        "root_cause_diagnosis": "TRANSIENT",
        "previous_failure_count": 0,
        "total_previous_payments": 5,
        "successful_payments": 5,
        "failed_payments": 0,
        "historical_success_rate": 1.0,
        "customer_tenure": 300,
        "average_transaction_amount": 4000.0,
        "previous_intervention_count": 0,
        "previous_successful_recoveries": 0,
        "historical_recovery_rate": 0.0,
        "time_since_last_intervention": None,
        "subscription_status": "NONE",
        "previous_subscription_failures": 0,
        "customer_name": "Demo User",
        "customer_notes": "Customer asked to retry"
    }
    
    available_actions = [
        "retry_payment",
        "payment_link",
        "reminder",
        "subscription_recovery",
        "human_escalation",
        "no_action"
    ]
    
    print("\n[Orchestrator Pipeline Started]")
    result = orchestrator.process_recovery_opportunity(event_id, mock_opportunity, available_actions)
    
    print("\n=== PIPELINE RESULTS ===")
    print("1. ML Prediction:")
    ml_prob = result['ml_probability']
    expected = ml_prob * mock_opportunity["amount"]
    print(f"   Probability: {ml_prob}")
    print(f"   Expected Value: {expected}")
    
    print("\n2. LLM Recommendation:")
    print(f"   Action: {result['llm_recommendation'].get('decision')}")
    print(f"   Confidence: {result['llm_recommendation'].get('confidence')}")
    
    print("\n3. Policy Decision:")
    print(f"   Allowed: {result['policy_decision'].get('allowed')}")
    print(f"   Reason: {result['policy_decision'].get('reason')}")
    
    print("\n4. Execution Result:")
    print(f"   Status: {result['execution_result'].get('status')}")
    print(f"   Reason: {result['execution_result'].get('reason')}")
    
    attempt_id = result['execution_result'].get('attempt_id')
    
    print("\n[Simulating Webhook: payment.captured]")
    # 4. Simulate a payment.captured webhook arriving
    webhook_event = RazorpayWebhookEvent(
        event="payment.captured",
        account_id="acc_123",
        created_at=1234567890,
        payload={
            "payment": {
                "entity": {
                    "id": f"pay_new_{uuid.uuid4()}",
                    "amount": 500000, # 5000.0
                    "customer_id": customer_id,
                    "notes": {
                        "reference_id": attempt_id
                    }
                }
            }
        }
    )
    
    tracker_result = tracker.process_payment_outcome(webhook_event)
    
    print("\n=== OUTCOME RESULTS ===")
    outcome = db.query(RecoveryOutcome).filter(RecoveryOutcome.event_id == event_id).first()
    print(f"   Webhook Process Result: {tracker_result['status']}")
    print(f"   Final Status: {outcome.status if outcome else 'UNKNOWN'}")
    print(f"   Amount Recovered: {outcome.amount_recovered if outcome else 0.0}")
    
    metrics = tracker.get_revenue_metrics()
    print("\n=== REVENUE METRICS ===")
    print(f"   Total At Risk: {metrics['total_revenue_at_risk']}")
    print(f"   Actual Recovered: {metrics['actual_revenue_recovered']}")
    print(f"   Recovery Rate: {metrics['recovery_rate_percentage']}%")
    print(f"   Attempts: {metrics['total_attempts']}")
    print(f"   Success Rate: {metrics['recovery_success_rate']}%")

    # Prediction Error (Actual vs Expected)
    actual = outcome.amount_recovered if outcome else 0.0
    error = actual - expected
    print(f"\n=== PREDICTION ACCURACY ===")
    print(f"   Expected Value: {expected}")
    print(f"   Actual Value: {actual}")
    print(f"   Prediction Error: {error} ({'Overperformed' if error > 0 else 'Underperformed'})")

    db.close()
    
if __name__ == "__main__":
    run_phase5_demo()
