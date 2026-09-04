import logging
import uuid
import os
import time
from datetime import datetime
from sqlalchemy.orm import Session
from models.core import RecoveryAttempt, RecoveryOutcome, PaymentEvent
try:
    import razorpay
except ImportError:
    razorpay = None

logger = logging.getLogger(__name__)

class RecoveryExecutor:
    def __init__(self, db: Session):
        self.db = db
        self.rzp_client = None
        key_id = os.environ.get("RAZORPAY_KEY_ID")
        key_secret = os.environ.get("RAZORPAY_KEY_SECRET")
        if razorpay and key_id and key_secret:
            # ONLY use if these are explicitly test credentials
            if key_id.startswith("rzp_test_"):
                self.rzp_client = razorpay.Client(auth=(key_id, key_secret))
            else:
                logger.warning("RAZORPAY_KEY_ID does not start with 'rzp_test_'. Refusing to initialize client to prevent live financial transactions.")

    def execute_action(self, event_id: str, event_data: dict, action: str, guardrail_decision: dict) -> dict:
        """
        Executes a recovery action if and only if guardrails allow it.
        Implements idempotency.
        """
        if guardrail_decision.get("status") != "ALLOW":
            logger.warning(f"Execution blocked by guardrails: {guardrail_decision.get('reason')}")
            return {"status": "BLOCKED", "reason": guardrail_decision.get("reason")}

        # Idempotency check: check if this specific action was already executed recently for this event
        existing_attempt = self.db.query(RecoveryAttempt).filter(
            RecoveryAttempt.event_id == event_id,
            RecoveryAttempt.action == action,
            RecoveryAttempt.status.in_(["SUCCESS", "PENDING", "FAILED"])
        ).order_by(RecoveryAttempt.created_at.desc()).first()

        if existing_attempt:
            # Extremely simple idempotency: if it was tried in the last 10 minutes, return the previous outcome
            time_diff = datetime.utcnow() - existing_attempt.created_at
            if time_diff.total_seconds() < 600:
                logger.info(f"Idempotent request detected for event '{event_id}', action '{action}'.")
                return {"status": "IDEMPOTENT", "attempt_id": existing_attempt.id, "previous_status": existing_attempt.status}

        attempt_id = str(uuid.uuid4())
        
        # 1. Initialize attempt record
        attempt = RecoveryAttempt(
            id=attempt_id,
            event_id=event_id,
            action=action,
            status="PENDING"
        )
        self.db.add(attempt)
        self.db.commit()

        # 2. Execute Action
        result_status = "FAILED"
        result_reason = ""
        
        try:
            if action == "payment_link":
                if not self.rzp_client:
                    result_status = "NOT_EXECUTABLE"
                    result_reason = "Razorpay test client not configured."
                else:
                    payment_entity = event_data.get("payment", {}).get("entity", {})
                    # Razorpay amounts are in paise.
                    raw_amount = payment_entity.get("amount", event_data.get("amount", 0))
                    amount = int(raw_amount)
                    currency = payment_entity.get("currency", event_data.get("currency", "INR"))
                    # Real test API call to Razorpay to create a payment link
                    response = self.rzp_client.payment_link.create({
                        "amount": amount,
                        "currency": currency,
                        "accept_partial": False,
                        "description": "ReviveAI Payment Recovery",
                        "reference_id": attempt_id,
                        "customer": {
                            "name": event_data.get("customer_name", "Test Customer"),
                            "contact": "+919999999999",
                            "email": "test@example.com"
                        },
                        "notify": {"sms": False, "email": False}
                    })
                    result_status = "SUCCESS"
                    result_reason = f"Payment link created: {response.get('short_url')}"
                    
            elif action == "retry_payment":
                # Razorpay API doesn't allow arbitrary retries without saved tokens or mandates.
                # Standard one-time payments cannot be programmatically 'retried'.
                result_status = "NOT_EXECUTABLE"
                result_reason = "Standard payments cannot be forcefully retried via API without customer intervention or mandate."
                
            elif action == "reminder":
                result_status = "SUCCESS"
                result_reason = "Mocked email reminder successfully sent (No external API needed)."
                
            elif action == "human_escalation":
                result_status = "SUCCESS"
                result_reason = "Flagged for human review."
                
            elif action == "no_action":
                result_status = "SUCCESS"
                result_reason = "No action taken as requested."
                
            else:
                result_status = "NOT_EXECUTABLE"
                result_reason = f"Action {action} is not supported by executor."
                
        except Exception as e:
            logger.error(f"Executor failed for {action}: {e}")
            result_status = "FAILED"
            result_reason = str(e)

        # 3. Update attempt record
        attempt.status = result_status
        
        # 4. Update outcome record if needed
        outcome = self.db.query(RecoveryOutcome).filter(RecoveryOutcome.event_id == event_id).first()
        if not outcome:
            payment_entity = event_data.get("payment", {}).get("entity", {})
            raw_amount = payment_entity.get("amount", event_data.get("amount", 0))
            amount_risk = float(raw_amount) / 100.0 if raw_amount else 0.0
            outcome = RecoveryOutcome(
                id=str(uuid.uuid4()),
                event_id=event_id,
                amount_at_risk=amount_risk,
                status="IN_PROGRESS"
            )
            self.db.add(outcome)
            
        self.db.commit()
        return {"status": result_status, "reason": result_reason, "attempt_id": attempt_id}
