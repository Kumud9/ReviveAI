import os
import pickle
import pandas as pd
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from features import engineer_features

def load_artifacts():
    preprocessor_path = os.path.join(os.path.dirname(__file__), "models", "preprocessor.pkl")
    model_path = os.path.join(os.path.dirname(__file__), "models", "recovery_model.pkl")
    
    if not os.path.exists(preprocessor_path) or not os.path.exists(model_path):
        raise FileNotFoundError("Model artifacts not found. Please run ml/train.py first.")
        
    with open(preprocessor_path, "rb") as f:
        preprocessor = pickle.load(f)
    with open(model_path, "rb") as f:
        model = pickle.load(f)
        
    return preprocessor, model

def predict_recovery_probability(features_dict: dict) -> dict:
    """
    Predicts the recovery probability for a single opportunity.
    """
    preprocessor, model = load_artifacts()
    
    # Convert to DataFrame
    df = pd.DataFrame([features_dict])
    
    # Feature engineering
    X, _ = engineer_features(df, fit=False, preprocessor=preprocessor)
    
    # Predict
    prob = model.predict_proba(X)[0][1]
    
    amount = features_dict.get("amount", 0.0)
    expected_value = amount * prob
    
    return {
        "recovery_probability": round(float(prob), 4),
        "expected_recovery_value": round(float(expected_value), 2)
    }

if __name__ == "__main__":
    # Test inference
    test_opportunity = {
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
        "previous_subscription_failures": 0
    }
    
    result = predict_recovery_probability(test_opportunity)
    print("Inference Test Result:")
    print(result)
