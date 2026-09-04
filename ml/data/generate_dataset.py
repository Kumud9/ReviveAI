import csv
import random
import math
from datetime import datetime, timedelta

def generate_synthetic_dataset(num_rows=20000, random_state=42):
    random.seed(random_state)
    
    # Target file
    filename = "synthetic_recovery_data.csv"
    
    headers = [
        "intervention_timestamp", "amount", "currency", "payment_method",
        "transaction_hour", "transaction_day", "amount_relative_to_customer_average",
        "error_code", "root_cause_diagnosis", "previous_failure_count",
        "total_previous_payments", "successful_payments", "failed_payments",
        "historical_success_rate", "customer_tenure", "average_transaction_amount",
        "previous_intervention_count", "previous_successful_recoveries",
        "historical_recovery_rate", "time_since_last_intervention",
        "subscription_status", "previous_subscription_failures", "recovered"
    ]
    
    recovered_count = 0
    diagnoses = ["TRANSIENT", "HARD_DECLINE", "ABANDONMENT", "MANDATE_ISSUE", "NON_PAYMENT"]
    diagnosis_probs = [0.4, 0.3, 0.15, 0.1, 0.05]
    
    error_code_map = {
        "TRANSIENT": ["timeout", "network_error", "issuer_down"],
        "HARD_DECLINE": ["insufficient_funds", "card_declined", "invalid_card"],
        "ABANDONMENT": ["none"],
        "MANDATE_ISSUE": ["auth_failure", "mandate_failed"],
        "NON_PAYMENT": ["unknown"]
    }
    
    base_probs = {
        "TRANSIENT": 0.6,
        "HARD_DECLINE": 0.2,
        "ABANDONMENT": 0.4,
        "MANDATE_ISSUE": 0.5,
        "NON_PAYMENT": 0.1
    }

    now = datetime.now()
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for _ in range(num_rows):
            # amount
            amount = round(random.lognormvariate(7, 1), 2)
            currency = random.choices(["INR", "USD"], weights=[0.9, 0.1])[0]
            payment_method = random.choices(["upi", "card", "netbanking", "wallet"], weights=[0.6, 0.3, 0.05, 0.05])[0]
            
            # timestamp
            days_ago = random.uniform(0, 365)
            ts = now - timedelta(days=days_ago)
            intervention_timestamp = ts.isoformat()
            
            transaction_hour = ts.hour
            transaction_day = ts.weekday()
            
            customer_tenure = random.randint(1, 1000)
            total_previous_payments = random.randint(0, 100)
            
            hist_success_rate = random.betavariate(8, 2)
            successful_payments = int(total_previous_payments * hist_success_rate)
            failed_payments = total_previous_payments - successful_payments
            
            avg_transaction_amount = random.lognormvariate(7, 1)
            amount_relative = amount / avg_transaction_amount if avg_transaction_amount > 0 else 1.0
            
            previous_intervention_count = 0
            while random.random() < 0.6:  # simulate poisson-like
                previous_intervention_count += 1
                
            prev_successful_recoveries = int(previous_intervention_count * random.uniform(0, 0.8)) if previous_intervention_count > 0 else 0
            historical_recovery_rate = prev_successful_recoveries / previous_intervention_count if previous_intervention_count > 0 else 0.0
            time_since_last = random.uniform(1, 720) if previous_intervention_count > 0 else ""
            
            root_cause_diagnosis = random.choices(diagnoses, weights=diagnosis_probs)[0]
            error_code = random.choice(error_code_map[root_cause_diagnosis])
            
            subscription_status = random.choices(["ACTIVE", "PAST_DUE", "CANCELLED", "NONE"], weights=[0.1, 0.05, 0.01, 0.84])[0]
            previous_subscription_failures = random.randint(0, 3) if subscription_status != "NONE" else 0
            
            true_prob = base_probs[root_cause_diagnosis]
            true_prob += (hist_success_rate - 0.8) * 0.2
            true_prob += (historical_recovery_rate - 0.4) * 0.3
            
            amt_pen = max(0, (amount_relative - 1.5) * 0.1)
            true_prob -= min(amt_pen, 0.3)
            
            true_prob -= min(previous_intervention_count * 0.05, 0.2)
            
            true_prob = max(0.01, min(0.95, true_prob))
            noise = random.gauss(0, 0.1)
            final_prob = max(0.01, min(0.99, true_prob + noise))
            
            recovered = 1 if random.random() < final_prob else 0
            recovered_count += recovered
            
            writer.writerow([
                intervention_timestamp, amount, currency, payment_method,
                transaction_hour, transaction_day, amount_relative,
                error_code, root_cause_diagnosis, previous_intervention_count,
                total_previous_payments, successful_payments, failed_payments,
                hist_success_rate, customer_tenure, avg_transaction_amount,
                previous_intervention_count, prev_successful_recoveries,
                historical_recovery_rate, time_since_last,
                subscription_status, previous_subscription_failures, recovered
            ])
            
    print(f"Dataset generated. Shape: ({num_rows}, {len(headers)})")
    print(f"Overall recovery rate: {recovered_count/num_rows:.2%}")
    print(f"Total recovered: {recovered_count}")
    print(f"Total not recovered: {num_rows - recovered_count}")

if __name__ == "__main__":
    generate_synthetic_dataset()
