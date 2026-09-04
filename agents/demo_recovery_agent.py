import sys
import os

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml.predict import predict_recovery_probability
from services.llm_client import LLMClient
from agents.recovery_agent import RecoveryAgent
import json

def run_demo():
    print("--- ReviveAI: LLM Recovery Agent Demo ---")
    
    # 1. Provide a mock payment opportunity
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
        "customer_notes": "Customer asked to retry but it timed out"
    }
    
    available_actions = [
        "retry_payment",
        "payment_link",
        "reminder",
        "subscription_recovery",
        "human_escalation",
        "no_action"
    ]
    
    print("\n1. Generating ML Prediction...")
    try:
        ml_prediction = predict_recovery_probability(mock_opportunity)
        probability = ml_prediction["recovery_probability"]
        expected_value = ml_prediction["expected_recovery_value"]
        print(f"   Probability: {probability}")
        print(f"   Expected Value: {expected_value}")
    except Exception as e:
        print(f"   [Error calling ML]: {e}")
        print("   Using fallback ML prediction for demo purposes.")
        probability = 0.85
        expected_value = 4250.0

    print("\n2. Initializing LLM Agent...")
    # This will use the mocked client if no API key is present
    client = LLMClient() 
    if client.is_configured():
        print("   [INFO] Real OpenAI client configured.")
    else:
        print("   [INFO] No API key found. Using Mocked LLM Client.")
        
    agent = RecoveryAgent(client)
    
    print("\n3. Investigating Opportunity...")
    recommendation = agent.investigate_recovery(
        payment_data=mock_opportunity,
        ml_probability=probability,
        expected_value=expected_value,
        available_actions=available_actions
    )
    
    print("\n4. Final Recommendation:")
    print(json.dumps(recommendation, indent=2))
    
if __name__ == "__main__":
    run_demo()
