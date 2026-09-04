from services.executor import RecoveryExecutor
from services.audit import log_audit_event
from models.core import PaymentEvent, RecoveryAttempt, AuditLog
import pytest

def test_executor_simulated_action(db_session):
    event = PaymentEvent(id="ev_exec_1", payload={"payment": {"entity": {"amount": 10000}}})
    db_session.add(event)
    db_session.commit()
    
    executor = RecoveryExecutor(db_session)
    result = executor.execute_action(event, "retry_payment")
    
    assert result["status"] == "SUCCESS_SIMULATED"
    
    attempt = db_session.query(RecoveryAttempt).filter_by(event_id=event.id).first()
    assert attempt is not None
    assert attempt.action == "retry_payment"

def test_audit_logging(db_session):
    log_audit_event(db_session, "ev_audit_1", "ref_1", "TEST_ACTION", "PROCEED", "Testing audit")
    
    log = db_session.query(AuditLog).filter_by(event_id="ev_audit_1").first()
    assert log is not None
    assert log.action_type == "TEST_ACTION"
    assert log.decision == "PROCEED"
