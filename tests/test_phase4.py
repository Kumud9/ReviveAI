import unittest
import uuid
import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.base import Base
from models.core import RecoveryAttempt, AuditLog
from engines.recovery_policy import RecoveryPolicyEngine
from engines.recovery_guardrails import RecoveryGuardrails
from services.executor import RecoveryExecutor
from services.orchestrator import RecoveryOrchestrator

class MockMLPredictor:
    def __call__(self, event_data):
        return {"recovery_probability": 0.8, "expected_recovery_value": 4000.0}

class MockLLMAgent:
    def __init__(self, override_decision="payment_link", confidence=0.9):
        self.decision = override_decision
        self.confidence = confidence

    def investigate_recovery(self, event_data, prob, ev, actions):
        return {
            "decision": self.decision,
            "confidence": self.confidence,
            "reason": "Mocked reason",
            "priority": "medium",
            "estimated_recovery_value": ev,
            "requires_human_review": False,
            "evidence": []
        }

class TestPhase4(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.db = self.Session()
        
        self.available_actions = [
            "retry_payment", 
            "payment_link", 
            "reminder", 
            "subscription_recovery", 
            "human_escalation",
            "no_action"
        ]
        self.base_event_data = {
            "amount": 5000.0,
            "currency": "INR",
            "status": "failed",
            "customer_name": "Test User"
        }
        self.event_id = str(uuid.uuid4())

    def tearDown(self):
        self.db.close()

    def get_orchestrator(self, llm_decision="payment_link", llm_confidence=0.9):
        executor = RecoveryExecutor(self.db)
        # Prevent actual Razorpay initialization during unit tests
        executor.rzp_client = None 
        return RecoveryOrchestrator(
            db=self.db,
            ml_predictor=MockMLPredictor(),
            llm_agent=MockLLMAgent(llm_decision, llm_confidence),
            executor=executor
        )

    def test_1_valid_action_allow(self):
        orch = self.get_orchestrator(llm_decision="payment_link")
        res = orch.process_recovery_opportunity(self.event_id, self.base_event_data, self.available_actions)
        
        self.assertTrue(res["policy_decision"]["allowed"])
        self.assertEqual(res["guardrail_decision"]["status"], "ALLOW")
        self.assertIn(res["execution_result"]["status"], ["SUCCESS", "NOT_EXECUTABLE", "FAILED"]) # Not blocked

    def test_2_invalid_action_deny(self):
        orch = self.get_orchestrator(llm_decision="invalid_action_123")
        res = orch.process_recovery_opportunity(self.event_id, self.base_event_data, self.available_actions)
        
        # Policy passes it because it doesn't filter actions, Guardrail denies it
        self.assertEqual(res["guardrail_decision"]["status"], "DENY")
        self.assertEqual(res["execution_result"]["status"], "NOT_EXECUTED")

    def test_3_max_attempts_reached(self):
        orch = self.get_orchestrator()
        # Seed 3 previous attempts
        for _ in range(3):
            att = RecoveryAttempt(id=str(uuid.uuid4()), event_id=self.event_id, action="payment_link", status="FAILED", created_at=datetime.utcnow() - timedelta(hours=2))
            self.db.add(att)
        self.db.commit()
        
        res = orch.process_recovery_opportunity(self.event_id, self.base_event_data, self.available_actions)
        self.assertFalse(res["policy_decision"]["allowed"])
        self.assertEqual(res["policy_decision"]["reason"], "Maximum of 3 attempts reached.")
        self.assertEqual(res["guardrail_decision"]["status"], "DENY")
        self.assertEqual(res["execution_result"]["status"], "NOT_EXECUTED")

    def test_4_cooldown_active(self):
        orch = self.get_orchestrator()
        # Seed attempt 5 mins ago
        att = RecoveryAttempt(id=str(uuid.uuid4()), event_id=self.event_id, action="payment_link", status="FAILED", created_at=datetime.utcnow() - timedelta(minutes=5))
        self.db.add(att)
        self.db.commit()
        
        res = orch.process_recovery_opportunity(self.event_id, self.base_event_data, self.available_actions)
        self.assertFalse(res["policy_decision"]["allowed"])
        self.assertTrue("Cooldown" in res["policy_decision"]["reason"])

    def test_5_already_recovered(self):
        orch = self.get_orchestrator()
        event_data = self.base_event_data.copy()
        event_data["status"] = "captured"
        
        res = orch.process_recovery_opportunity(self.event_id, event_data, self.available_actions)
        self.assertFalse(res["policy_decision"]["allowed"])
        self.assertEqual(res["execution_result"]["status"], "NOT_EXECUTED")

    def test_6_high_value(self):
        orch = self.get_orchestrator()
        event_data = self.base_event_data.copy()
        event_data["amount"] = 500000.0 # High value
        
        res = orch.process_recovery_opportunity(self.event_id, event_data, self.available_actions)
        self.assertFalse(res["policy_decision"]["allowed"])
        self.assertTrue(res["policy_decision"]["requires_human_review"])
        self.assertEqual(res["guardrail_decision"]["status"], "HUMAN_REVIEW")

    def test_7_low_confidence(self):
        orch = self.get_orchestrator(llm_confidence=0.4)
        res = orch.process_recovery_opportunity(self.event_id, self.base_event_data, self.available_actions)
        self.assertTrue(res["policy_decision"]["requires_human_review"])

    def test_8_duplicate_idempotent(self):
        orch = self.get_orchestrator()
        # Create an attempt marked as PENDING very recently
        att_id = str(uuid.uuid4())
        att = RecoveryAttempt(id=att_id, event_id=self.event_id, action="payment_link", status="PENDING", created_at=datetime.utcnow())
        self.db.add(att)
        self.db.commit()
        
        # Policy is fine, Guardrail should DENY because an action is already IN_PROGRESS/PENDING
        res = orch.process_recovery_opportunity(self.event_id, self.base_event_data, self.available_actions)
        self.assertEqual(res["guardrail_decision"]["status"], "DENY")
        
        # Now bypass guardrail logic explicitly for executor test
        executor = RecoveryExecutor(self.db)
        executor.rzp_client = None
        exec_res = executor.execute_action(self.event_id, self.base_event_data, "payment_link", {"status": "ALLOW"})
        self.assertEqual(exec_res["status"], "IDEMPOTENT")

    def test_9_policy_rejection(self):
        orch = self.get_orchestrator(llm_decision="no_action")
        res = orch.process_recovery_opportunity(self.event_id, self.base_event_data, self.available_actions)
        self.assertFalse(res["policy_decision"]["allowed"])

    def test_10_guardrail_rejection(self):
        orch = self.get_orchestrator(llm_decision="payment_link")
        event_data = self.base_event_data.copy()
        event_data["amount"] = -500.0 # Negative amount
        res = orch.process_recovery_opportunity(self.event_id, event_data, self.available_actions)
        self.assertEqual(res["guardrail_decision"]["status"], "DENY")
        
    def test_11_executor_failure(self):
        orch = self.get_orchestrator(llm_decision="payment_link")
        res = orch.process_recovery_opportunity(self.event_id, self.base_event_data, self.available_actions)
        # Without real Razorpay client, it returns NOT_EXECUTABLE
        self.assertEqual(res["execution_result"]["status"], "NOT_EXECUTABLE")
        
        # Audit Log should contain ACTION_EXECUTION
        logs = self.db.query(AuditLog).filter(AuditLog.event_id == self.event_id, AuditLog.action_type == "ACTION_EXECUTION").all()
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].decision, "NOT_EXECUTABLE")

if __name__ == '__main__':
    unittest.main()
