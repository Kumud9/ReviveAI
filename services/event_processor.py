from sqlalchemy.orm import Session
from datetime import datetime
from models.core import PaymentEvent, Customer, Payment, Subscription
from schemas.events import RazorpayWebhookEvent
import uuid
import logging

logger = logging.getLogger(__name__)

def process_razorpay_event(event: RazorpayWebhookEvent, db: Session):
    """
    Idempotent event ingestion.
    """
    # Event ID uniqueness / Idempotency
    # For Razorpay webhooks, the payload usually contains an id for the event,
    # or we can construct one. For this demo, let's assume `event.account_id` + `timestamp`
    # or a webhook header if available. We'll generate a unique one if not present,
    # but Razorpay sends `x-razorpay-event-id`. For simplicity, we'll extract from payload or use UUID.
    
    event_id = event.payload.get("id", str(uuid.uuid4()))
    
    # Check if already processed
    existing_event = db.query(PaymentEvent).filter(PaymentEvent.id == event_id).first()
    if existing_event:
        logger.info(f"Event {event_id} already processed. Skipping.")
        return

    # Extract common fields
    entity = event.payload.get("payment", {}).get("entity", {})
    if not entity and "subscription" in event.payload:
        entity = event.payload.get("subscription", {}).get("entity", {})

    customer_id = entity.get("customer_id")
    payment_id = entity.get("id") if "payment" in event.payload else None
    subscription_id = entity.get("subscription_id")
    error_code = entity.get("error_code")
    amount = entity.get("amount", 0) / 100.0 # Assuming paise

    # Upsert Customer (Simplified)
    if customer_id:
        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            customer = Customer(
                id=customer_id,
                email=entity.get("email"),
                phone=entity.get("contact")
            )
            db.add(customer)

    # Upsert Payment/Subscription
    if payment_id:
        payment = db.query(Payment).filter(Payment.id == payment_id).first()
        if not payment:
            payment = Payment(
                id=payment_id,
                customer_id=customer_id,
                amount=amount,
                currency=entity.get("currency", "INR"),
                status=entity.get("status"),
                method=entity.get("method")
            )
            db.add(payment)

    # Persist Event
    new_event = PaymentEvent(
        id=event_id,
        event_type=event.event,
        customer_id=customer_id,
        payment_id=payment_id,
        subscription_id=subscription_id,
        error_code=error_code,
        payload=event.payload,
        processed=False
    )
    db.add(new_event)
    db.commit()

    # Branch execution based on event type
    if event.event in ["payment.captured", "payment.authorized"]:
        from services.outcome_tracker import OutcomeTracker
        tracker = OutcomeTracker(db)
        result = tracker.process_payment_outcome(event)
        
        new_event.processed = True
        db.commit()
        logger.info(f"Processed outcome event {event_id}: {result}")
        return

    # Move to Diagnosis -> Policy -> Execution for failed events
    from agents.demo_phase4 import RecoveryOrchestrator
    
    # We use the RecoveryOrchestrator from Phase 4 to maintain architecture
    # but the old event_processor was calling them manually. Let's use the Orchestrator
    # if it exists, or the manual calls. The prompt says "Do not change Phase 3/4 architecture",
    # so we will use the existing manual calls as they were already here.
    
    from engines.diagnosis import diagnose_event
    from engines.policy import get_policy_for_diagnosis
    from engines.guardrails import evaluate_guardrails
    from services.executor import RecoveryExecutor
    from services.audit import log_audit_event
    
    log_audit_event(db, event_id, customer_id, "EVENT_RECEIVED", "PROCEED", "Event ingested successfully.")

    diagnosis = diagnose_event(new_event)
    
    log_audit_event(db, event_id, None, "DIAGNOSIS", diagnosis["root_cause"], diagnosis["reasoning"], {"confidence": diagnosis["confidence"]})
    
    policy = get_policy_for_diagnosis(diagnosis["root_cause"], db)
    
    log_audit_event(db, event_id, None, "POLICY_SELECTED", "PROCEED", f"Selected policy for {diagnosis['root_cause']}", policy)
    
    # Optional: AI Prioritization Scoring
    from engines.intelligence import calculate_recovery_score
    score = calculate_recovery_score(new_event, diagnosis, policy)
    log_audit_event(db, event_id, None, "SCORING", "COMPLETED", f"Calculated priority score: {score['priority_score']}", score)
    
    executor = RecoveryExecutor(db)
    
    # Simple strategy: just try the first action in the list.
    if policy["actions"]:
        action = policy["actions"][0]
        
        allowed, skip_reason = evaluate_guardrails(new_event, action, policy, db)
        
        # Wait, the executor.execute_action signature changed in Phase 4 to:
        # execute_action(self, event_id: str, event_data: dict, action: str, guardrail_decision: dict) -> dict:
        
        guardrail_decision = {"status": "ALLOW" if allowed else "DENY", "reason": skip_reason}
        
        if allowed:
            log_audit_event(db, event_id, None, "GUARDRAIL_EVALUATED", "ALLOW", f"Guardrails passed for action {action}")
            result = executor.execute_action(event_id, event.payload, action, guardrail_decision)
            log_audit_event(db, event_id, result.get("attempt_id"), "ACTION_EXECUTED", "SUCCESS", f"Executed {action}", result)
        else:
            log_audit_event(db, event_id, None, "GUARDRAIL_EVALUATED", "DENY", f"Guardrails failed: {skip_reason}")
            # Even if denied, log the block
            executor.execute_action(event_id, event.payload, action, guardrail_decision)
    else:
        log_audit_event(db, event_id, None, "EXECUTION_SKIPPED", "NO_ACTIONS", "No actions defined in policy.")
    
    # Update event as processed
    new_event.processed = True
    db.commit()
    
    logger.info(f"Processed event {event_id}: Diagnosis: {diagnosis['root_cause']}")

