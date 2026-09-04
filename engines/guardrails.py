from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from models.core import PaymentEvent, Customer, Payment, RecoveryAttempt, RecoveryPolicy

def evaluate_guardrails(event: PaymentEvent, action: str, policy: dict, db: Session) -> tuple[bool, str]:
    """
    Evaluates hard guardrails before any recovery action is executed.
    Returns: (allowed: bool, skip_reason: str)
    """
    # 1. Check if already paid (Race Condition Protection)
    if event.payment_id:
        payment = db.query(Payment).filter(Payment.id == event.payment_id).first()
        if payment and payment.status == "captured":
            return False, "ALREADY_PAID"

    # 2. Check DND / Opt-out
    if event.customer_id:
        customer = db.query(Customer).filter(Customer.id == event.customer_id).first()
        if customer and customer.dnd:
            return False, "CUSTOMER_DND"

    # 3. Check Action Allowed
    if action not in policy.get("actions", []):
        return False, "ACTION_NOT_ALLOWED_BY_POLICY"

    # Get previous attempts for this event
    attempts = db.query(RecoveryAttempt).filter(RecoveryAttempt.event_id == event.id).order_by(RecoveryAttempt.created_at.desc()).all()

    # 4. Check Maximum Attempts
    max_attempts = policy.get("max_attempts", 0)
    if len(attempts) >= max_attempts:
        return False, "MAX_ATTEMPTS_REACHED"

    # 5. Check Cooldown
    if attempts:
        last_attempt = attempts[0]
        cooldown_hours_list = policy.get("cooldown_hours", [])
        
        # Determine applicable cooldown based on attempt number
        attempt_idx = min(len(attempts) - 1, len(cooldown_hours_list) - 1)
        if attempt_idx >= 0:
            required_cooldown = cooldown_hours_list[attempt_idx]
            elapsed_time = datetime.utcnow() - last_attempt.created_at
            if elapsed_time < timedelta(hours=required_cooldown):
                return False, "COOLDOWN_NOT_ELAPSED"

    return True, ""
