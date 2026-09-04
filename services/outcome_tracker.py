from sqlalchemy.orm import Session
from datetime import datetime
import logging

from models.core import RecoveryOutcome, RecoveryAttempt, PaymentEvent
from schemas.events import RazorpayWebhookEvent

logger = logging.getLogger(__name__)

class OutcomeTracker:
    def __init__(self, db: Session):
        self.db = db

    def process_payment_outcome(self, event: RazorpayWebhookEvent):
        """
        Idempotent outcome processing for payment.captured or payment.authorized.
        """
        entity = event.payload.get("payment", {}).get("entity", {})
        if not entity:
            return {"status": "ignored", "reason": "No payment entity found"}

        payment_id = entity.get("id")
        amount = entity.get("amount", 0) / 100.0
        currency = entity.get("currency", "INR")
        customer_id = entity.get("customer_id")
        notes = entity.get("notes", {})
        reference_id = notes.get("reference_id")

        outcome = self._find_recovery_outcome(payment_id, reference_id, customer_id, amount)

        if not outcome:
            return {"status": "ignored", "reason": "No corresponding recovery outcome found"}

        if outcome.status == "RECOVERED":
            return {"status": "idempotent", "reason": "Already marked recovered"}

        # If it's captured/authorized, mark as recovered
        if event.event in ["payment.captured", "payment.authorized"]:
            # If we matched via fallback, mark as UNVERIFIED, else RECOVERED
            if getattr(outcome, '_is_fallback_match', False):
                outcome.status = "UNVERIFIED"
            else:
                outcome.status = "RECOVERED"
            
            outcome.amount_recovered = amount
            outcome.recovered_at = datetime.utcnow()
            
            # If the amount recovered is less than amount at risk, flag it for analytics
            if amount < outcome.amount_at_risk:
                logger.warning(f"Partial recovery: {amount} < {outcome.amount_at_risk}")
                # We can store a metadata flag if we had a JSON field, but status suffices
                if outcome.status == "RECOVERED":
                    outcome.status = "RECOVERED_PARTIAL"

            self.db.commit()
            return {"status": "processed", "outcome_status": outcome.status}

        return {"status": "ignored", "reason": f"Unhandled event type {event.event}"}

    def _find_recovery_outcome(self, payment_id: str, reference_id: str, customer_id: str, amount: float):
        # 1. Razorpay payment ID (If exact same payment was somehow retried)
        if payment_id:
            # PaymentEvent -> RecoveryOutcome
            event_rec = self.db.query(PaymentEvent).filter(PaymentEvent.payment_id == payment_id).first()
            if event_rec:
                outcome = self.db.query(RecoveryOutcome).filter(RecoveryOutcome.event_id == event_rec.id).first()
                if outcome:
                    return outcome

        # 2. Recovery attempt reference ID (from payment_link reference_id)
        if reference_id:
            attempt = self.db.query(RecoveryAttempt).filter(RecoveryAttempt.id == reference_id).first()
            if attempt:
                outcome = self.db.query(RecoveryOutcome).filter(RecoveryOutcome.event_id == attempt.event_id).first()
                if outcome:
                    return outcome

        # 3. Fallback: customer + amount
        if customer_id and amount > 0:
            # Find IN_PROGRESS outcome for this customer and amount
            # Requires a join with PaymentEvent
            outcome = self.db.query(RecoveryOutcome).join(PaymentEvent).filter(
                PaymentEvent.customer_id == customer_id,
                RecoveryOutcome.amount_at_risk == amount,
                RecoveryOutcome.status == "IN_PROGRESS"
            ).order_by(RecoveryOutcome.id.desc()).first()
            
            if outcome:
                outcome._is_fallback_match = True
                return outcome

        return None

    def get_revenue_metrics(self) -> dict:
        """
        Calculate and return Phase 5 Analytics.
        """
        outcomes = self.db.query(RecoveryOutcome).all()
        
        total_at_risk = sum(o.amount_at_risk for o in outcomes if o.amount_at_risk)
        total_recovered = sum(o.amount_recovered for o in outcomes if o.status in ["RECOVERED", "RECOVERED_PARTIAL"])
        
        attempts_count = self.db.query(RecoveryAttempt).count()
        success_count = sum(1 for o in outcomes if o.status in ["RECOVERED", "RECOVERED_PARTIAL"])
        
        recovery_rate = (total_recovered / total_at_risk * 100) if total_at_risk > 0 else 0.0
        success_rate = (success_count / len(outcomes) * 100) if outcomes else 0.0
        
        return {
            "total_revenue_at_risk": round(total_at_risk, 2),
            "actual_revenue_recovered": round(total_recovered, 2),
            "recovery_rate_percentage": round(recovery_rate, 2),
            "total_opportunities": len(outcomes),
            "total_attempts": attempts_count,
            "successful_recoveries": success_count,
            "recovery_success_rate": round(success_rate, 2)
        }
