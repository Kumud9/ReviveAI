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

from models.base import Base
from models.core import AuditLog
from ml.predict import predict_recovery_probability
from services.llm_client import LLMClient
from agents.recovery_agent import RecoveryAgent
from services.executor import RecoveryExecutor
from services.orchestrator import RecoveryOrchestrator

def run_phase4_demo():
    print("--- ReviveAI: Phase 4 End-to-End Orchestration Demo ---")
    
    # 1. Setup DB
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # 2. Setup Services
    load_dotenv(override=True)
    client = LLMClient() 
    if not client.is_configured():
        print("[WARNING] Real LLM client not configured. Falling back to mock for deterministic demo.")
        
    llm_agent = RecoveryAgent(client)
    executor = RecoveryExecutor(db)
    
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
    mock_opportunity = {
        "amount": 5000.0,
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
    print(f"   Probability: {result['ml_probability']}")
    
    print("\n2. LLM Recommendation:")
    print(f"   Action: {result['llm_recommendation'].get('decision')}")
    print(f"   Confidence: {result['llm_recommendation'].get('confidence')}")
    
    print("\n3. Policy Decision:")
    print(f"   Allowed: {result['policy_decision'].get('allowed')}")
    print(f"   Reason: {result['policy_decision'].get('reason')}")
    
    print("\n4. Guardrails Decision:")
    print(f"   Status: {result['guardrail_decision'].get('status')}")
    print(f"   Reason: {result['guardrail_decision'].get('reason')}")
    
    print("\n5. Execution Result:")
    print(f"   Status: {result['execution_result'].get('status')}")
    print(f"   Reason: {result['execution_result'].get('reason')}")
    
    print("\n=== AUDIT TRAIL ===")
    logs = db.query(AuditLog).filter(AuditLog.event_id == event_id).order_by(AuditLog.id.asc()).all()
    for log in logs:
        print(f"[{log.created_at}] {log.action_type} -> {log.decision} ({log.reasoning})")
        
    db.close()
    
if __name__ == "__main__":
    run_phase4_demo()
