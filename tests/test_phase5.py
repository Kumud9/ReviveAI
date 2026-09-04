import unittest
import os
import uuid
import warnings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.base import Base
from models.core import Customer, PaymentEvent, RecoveryOutcome, RecoveryAttempt
from schemas.events import RazorpayWebhookEvent
from services.outcome_tracker import OutcomeTracker

class TestPhase5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        warnings.filterwarnings("ignore", category=UserWarning)
        cls.engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(bind=cls.engine)
        cls.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    def setUp(self):
        self.db = self.SessionLocal()
        # Clean db for each test
        for table in reversed(Base.metadata.sorted_tables):
            self.db.execute(table.delete())
        self.db.commit()
        
        self.tracker = OutcomeTracker(self.db)
        
        # Setup basic data
        self.customer_id = f"cust_{uuid.uuid4()}"
        self.db.add(Customer(id=self.customer_id, email="test@test.com"))
        
        self.failed_event_id = f"evt_{uuid.uuid4()}"
        self.payment_id = f"pay_{uuid.uuid4()}"
        
        self.db.add(PaymentEvent(
            id=self.failed_event_id,
            event_type="payment.failed",
            customer_id=self.customer_id,
            payment_id=self.payment_id,
            payload={}
        ))
        
        self.attempt_id = f"attempt_{uuid.uuid4()}"
        self.db.add(RecoveryAttempt(
            id=self.attempt_id,
            event_id=self.failed_event_id,
            action="payment_link",
            status="SUCCESS"
        ))
        
        self.outcome_id = f"out_{uuid.uuid4()}"
        self.db.add(RecoveryOutcome(
            id=self.outcome_id,
            event_id=self.failed_event_id,
            amount_at_risk=1000.0,
            status="IN_PROGRESS"
        ))
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def test_successful_recovery_via_reference_id(self):
        # Webhook payload with reference_id matching attempt_id
        event = RazorpayWebhookEvent(
            event="payment.captured",
            account_id="acc_123",
            created_at=1234567890,
            payload={
                "payment": {
                    "entity": {
                        "id": f"pay_new_{uuid.uuid4()}",
                        "amount": 100000, # paise -> 1000.0
                        "customer_id": self.customer_id,
                        "notes": {
                            "reference_id": self.attempt_id
                        }
                    }
                }
            }
        )
        
        res = self.tracker.process_payment_outcome(event)
        self.assertEqual(res["status"], "processed")
        self.assertEqual(res["outcome_status"], "RECOVERED")
        
        outcome = self.db.query(RecoveryOutcome).filter(RecoveryOutcome.id == self.outcome_id).first()
        self.assertEqual(outcome.status, "RECOVERED")
        self.assertEqual(outcome.amount_recovered, 1000.0)

    def test_successful_recovery_via_payment_id(self):
        # Webhook payload where payment ID matches the original failed payment exactly
        event = RazorpayWebhookEvent(
            event="payment.authorized",
            account_id="acc_123",
            created_at=1234567890,
            payload={
                "payment": {
                    "entity": {
                        "id": self.payment_id,
                        "amount": 100000,
                        "customer_id": self.customer_id
                    }
                }
            }
        )
        
        res = self.tracker.process_payment_outcome(event)
        self.assertEqual(res["status"], "processed")
        
        outcome = self.db.query(RecoveryOutcome).filter(RecoveryOutcome.id == self.outcome_id).first()
        self.assertEqual(outcome.status, "RECOVERED")
        self.assertEqual(outcome.amount_recovered, 1000.0)

    def test_partial_recovery(self):
        event = RazorpayWebhookEvent(
            event="payment.captured",
            account_id="acc_123",
            created_at=1234567890,
            payload={
                "payment": {
                    "entity": {
                        "id": f"pay_new_{uuid.uuid4()}",
                        "amount": 50000, # paise -> 500.0, less than 1000.0
                        "customer_id": self.customer_id,
                        "notes": {
                            "reference_id": self.attempt_id
                        }
                    }
                }
            }
        )
        
        res = self.tracker.process_payment_outcome(event)
        self.assertEqual(res["status"], "processed")
        
        outcome = self.db.query(RecoveryOutcome).filter(RecoveryOutcome.id == self.outcome_id).first()
        self.assertEqual(outcome.status, "RECOVERED_PARTIAL")
        self.assertEqual(outcome.amount_recovered, 500.0)

    def test_unverified_fallback_recovery(self):
        # Payload with no matching reference_id or payment_id, but matching customer and amount
        event = RazorpayWebhookEvent(
            event="payment.captured",
            account_id="acc_123",
            created_at=1234567890,
            payload={
                "payment": {
                    "entity": {
                        "id": f"pay_unknown_{uuid.uuid4()}",
                        "amount": 100000,
                        "customer_id": self.customer_id
                    }
                }
            }
        )
        
        res = self.tracker.process_payment_outcome(event)
        self.assertEqual(res["status"], "processed")
        
        outcome = self.db.query(RecoveryOutcome).filter(RecoveryOutcome.id == self.outcome_id).first()
        self.assertEqual(outcome.status, "UNVERIFIED")

    def test_duplicate_outcome(self):
        outcome = self.db.query(RecoveryOutcome).filter(RecoveryOutcome.id == self.outcome_id).first()
        outcome.status = "RECOVERED"
        self.db.commit()
        
        event = RazorpayWebhookEvent(
            event="payment.captured",
            account_id="acc_123",
            created_at=1234567890,
            payload={
                "payment": {
                    "entity": {
                        "id": f"pay_new_{uuid.uuid4()}",
                        "amount": 100000,
                        "customer_id": self.customer_id,
                        "notes": {
                            "reference_id": self.attempt_id
                        }
                    }
                }
            }
        )
        
        res = self.tracker.process_payment_outcome(event)
        self.assertEqual(res["status"], "idempotent")

    def test_unknown_outcome(self):
        # Non-matching event
        event = RazorpayWebhookEvent(
            event="payment.captured",
            account_id="acc_123",
            created_at=1234567890,
            payload={
                "payment": {
                    "entity": {
                        "id": f"pay_unknown_{uuid.uuid4()}",
                        "amount": 500000,
                        "customer_id": f"cust_other_{uuid.uuid4()}"
                    }
                }
            }
        )
        
        res = self.tracker.process_payment_outcome(event)
        self.assertEqual(res["status"], "ignored")

    def test_revenue_metrics(self):
        # We have one IN_PROGRESS outcome with 1000 at risk
        self.db.add(RecoveryOutcome(
            id=f"out_2_{uuid.uuid4()}",
            event_id=self.failed_event_id,
            amount_at_risk=2000.0,
            amount_recovered=2000.0,
            status="RECOVERED"
        ))
        
        self.db.add(RecoveryOutcome(
            id=f"out_3_{uuid.uuid4()}",
            event_id=self.failed_event_id,
            amount_at_risk=500.0,
            amount_recovered=250.0,
            status="RECOVERED_PARTIAL"
        ))
        
        self.db.commit()
        
        metrics = self.tracker.get_revenue_metrics()
        
        self.assertEqual(metrics["total_revenue_at_risk"], 3500.0)
        self.assertEqual(metrics["actual_revenue_recovered"], 2250.0)
        self.assertEqual(metrics["total_opportunities"], 3)
        self.assertEqual(metrics["successful_recoveries"], 2)
        # 2 / 3 = 66.67%
        self.assertEqual(metrics["recovery_success_rate"], 66.67)
