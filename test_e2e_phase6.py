import os
import sys
import json
import hmac
import hashlib
import uuid
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

# Must import from app to get the DB and models
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from main import app
from models.base import engine, Base, SessionLocal
from models.core import PaymentEvent, AuditLog, RecoveryAttempt, RecoveryOutcome

# Ensure tables exist (on postgres)
Base.metadata.create_all(bind=engine)

client = TestClient(app)
webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "webhook_secret")

def sign_payload(payload: dict, secret: str) -> str:
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    return hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()

event_id = f"evt_{uuid.uuid4().hex}"
payment_id = f"pay_{uuid.uuid4().hex}"

payload = {
    "account_id": "acc_123",
    "event": "payment.failed",
    "payload": {
        "id": event_id,
        "payment": {
            "entity": {
                "id": payment_id,
                "amount": 100000, # 1000 INR
                "currency": "INR",
                "error_code": "BAD_REQUEST_ERROR",
                "error_description": "Payment failed due to customer dropping off",
                "customer_name": "Test User",
                "email": "test@example.com",
                "contact": "+919999999999"
            }
        }
    },
    "created_at": 1234567890
}

# 1. SEND WEBHOOK
print(f"--- STARTING E2E TEST FOR {event_id} ---")
sig = sign_payload(payload, webhook_secret)
response = client.post("/webhooks/razorpay", content=json.dumps(payload, separators=(',', ':')), headers={"x-razorpay-signature": sig})

print(f"Webhook HTTP Status: {response.status_code}")
print(f"Webhook Response: {response.json()}")

if response.status_code != 200:
    print("FAILED AT WEBHOOK")
    sys.exit(1)

db = SessionLocal()

# 2. CHECK PERSISTENCE
db_event = db.query(PaymentEvent).filter(PaymentEvent.id == event_id).first()
if not db_event:
    print("FAILED: Event not persisted in DB.")
    sys.exit(1)
else:
    print("Event Persisted: PASS")

# 3. CHECK AUDIT LOG (ML, LLM, Policy, Guardrails, Execution)
audits = db.query(AuditLog).filter(AuditLog.event_id == event_id).order_by(AuditLog.created_at.asc()).all()
audit_stages = [a.action_type for a in audits]

print(f"Audit Stages Traversed: {audit_stages}")

# Extract decisions
diagnosis = next((a for a in audits if a.action_type == "DIAGNOSIS"), None)
policy = next((a for a in audits if a.action_type == "POLICY_SELECTED"), None)
guardrail = next((a for a in audits if a.action_type == "GUARDRAIL_EVALUATED"), None)
execution = next((a for a in audits if a.action_type == "ACTION_EXECUTED" or a.action_type == "EXECUTION_SKIPPED"), None)

if diagnosis:
    print(f"Diagnosis / Reason: {diagnosis.decision} ({diagnosis.reasoning})")
if policy:
    print(f"Policy Selected: {policy.reasoning}")
if guardrail:
    print(f"Guardrail Decision: {guardrail.decision} ({guardrail.reasoning})")
if execution:
    print(f"Execution Result: {execution.decision} ({execution.reasoning})")
    if execution.metadata_:
        print(f"Execution Metadata: {execution.metadata_}")

# 4. CHECK RECOVERY ATTEMPT
attempt = db.query(RecoveryAttempt).filter(RecoveryAttempt.event_id == event_id).first()
if attempt:
    print(f"Recovery Attempt Action: {attempt.action}, Status: {attempt.status}")

# 5. CHECK OUTCOME
outcome = db.query(RecoveryOutcome).filter(RecoveryOutcome.event_id == event_id).first()
if outcome:
    print(f"Amount at Risk: {outcome.amount_at_risk}")
    print(f"Actual Recovered: {outcome.amount_recovered}")
else:
    print("No Recovery Outcome tracked.")

# 6. IDEMPOTENCY TEST
print("\n--- RUNNING IDEMPOTENCY TEST ---")
response2 = client.post("/webhooks/razorpay", content=json.dumps(payload, separators=(',', ':')), headers={"x-razorpay-signature": sig})
print(f"Duplicate Webhook HTTP Status: {response2.status_code}")

attempts_count = db.query(RecoveryAttempt).filter(RecoveryAttempt.event_id == event_id).count()
if attempts_count > 1:
    print(f"FAILED: Idempotency check failed. Found {attempts_count} attempts.")
else:
    print(f"Idempotency Check: PASS ({attempts_count} attempt)")

db.close()
print("\n--- E2E TEST COMPLETE ---")
