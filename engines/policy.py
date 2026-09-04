from sqlalchemy.orm import Session
from models.core import RecoveryPolicy

# Default policies if not in DB
DEFAULT_POLICIES = {
    "TRANSIENT": {
        "actions": ["retry_payment"],
        "max_attempts": 3,
        "cooldown_hours": [1, 6, 24]
    },
    "HARD_DECLINE": {
        "actions": ["send_payment_update_link", "send_email_reminder"],
        "max_attempts": 2,
        "cooldown_hours": [24, 48]
    },
    "ABANDONMENT": {
        "actions": ["single_reminder_nudge"],
        "max_attempts": 1,
        "cooldown_hours": [1]
    },
    "MANDATE_ISSUE": {
        "actions": ["mandate_retry", "mandate_retry", "fallback_payment_link"],
        "max_attempts": 3,
        "cooldown_hours": [24, 72, 120]
    },
    "NON_PAYMENT": {
        "actions": ["email", "sms", "voice_call"],
        "max_attempts": 3,
        "cooldown_hours": [24, 72, 120]
    },
    "SUCCESS": {
        "actions": [],
        "max_attempts": 0,
        "cooldown_hours": []
    }
}

def get_policy_for_diagnosis(root_cause: str, db: Session) -> dict:
    """
    Retrieve the recovery policy for a given root cause.
    Checks DB first, falls back to defaults.
    """
    policy = db.query(RecoveryPolicy).filter(RecoveryPolicy.root_cause == root_cause).first()
    
    if policy:
        return {
            "actions": policy.actions,
            "max_attempts": policy.max_attempts,
            "cooldown_hours": policy.cooldown_hours
        }
        
    # Seed default into DB and return
    default_policy = DEFAULT_POLICIES.get(root_cause, DEFAULT_POLICIES["HARD_DECLINE"])
    new_policy = RecoveryPolicy(
        root_cause=root_cause,
        actions=default_policy["actions"],
        max_attempts=default_policy["max_attempts"],
        cooldown_hours=default_policy["cooldown_hours"]
    )
    db.add(new_policy)
    db.commit()
    return default_policy
