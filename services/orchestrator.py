import logging
from sqlalchemy.orm import Session
from models.core import RecoveryAttempt
from services.executor import RecoveryExecutor
from services.audit import log_audit_event
from engines.recovery_policy import RecoveryPolicyEngine
from engines.recovery_guardrails import RecoveryGuardrails

logger = logging.getLogger(__name__)

class RecoveryOrchestrator:
    def __init__(self, db: Session, ml_predictor, llm_agent, executor: RecoveryExecutor):
        self.db = db
        self.ml_predictor = ml_predictor
        self.llm_agent = llm_agent
        self.executor = executor
        self.policy_engine = RecoveryPolicyEngine(db_session=db)
        self.guardrails = RecoveryGuardrails()

    def process_recovery_opportunity(self, event_id: str, event_data: dict, available_actions: list) -> dict:
        """
        Orchestrates the full Phase 4 pipeline.
        1. Predict (ML)
        2. Recommend (LLM)
        3. Authorize (Policy)
        4. Validate (Guardrails)
        5. Execute (Executor)
        """
        logger.info(f"Orchestrator: Processing event {event_id}")
        
        # 1. ML Prediction
        ml_prediction = {"recovery_probability": 0.5, "expected_recovery_value": 0.0}
        if self.ml_predictor:
            try:
                ml_prediction = self.ml_predictor(event_data)
            except Exception as e:
                logger.error(f"ML predictor failed: {e}")
                
        # 2. LLM Recommendation
        llm_recommendation = {"decision": "human_escalation", "confidence": 0.0, "reason": "Default fallback"}
        if self.llm_agent:
            try:
                llm_recommendation = self.llm_agent.investigate_recovery(
                    event_data, 
                    ml_prediction["recovery_probability"], 
                    ml_prediction["expected_recovery_value"], 
                    available_actions
                )
            except Exception as e:
                logger.error(f"LLM agent failed: {e}")
                
        # Get Attempt History
        attempt_history = self.db.query(RecoveryAttempt).filter(
            RecoveryAttempt.event_id == event_id
        ).order_by(RecoveryAttempt.created_at.asc()).all()
        # Convert objects to dicts for the engine
        history_dicts = [{"action": a.action, "status": a.status, "created_at": a.created_at} for a in attempt_history]
        
        # 3. Policy Engine
        policy_decision = self.policy_engine.evaluate(event_data, ml_prediction["recovery_probability"], llm_recommendation, history_dicts)
        
        log_audit_event(
            self.db, event_id, None, "POLICY_EVALUATION", 
            "ALLOW" if policy_decision["allowed"] else "DENY", 
            policy_decision["reason"],
            {"action": policy_decision["action"]}
        )

        # 4. Guardrails
        guardrail_decision = self.guardrails.verify(policy_decision, event_data, history_dicts)
        
        log_audit_event(
            self.db, event_id, None, "GUARDRAIL_EVALUATION", 
            guardrail_decision["status"], 
            guardrail_decision["reason"],
            {"action": guardrail_decision["action"]}
        )

        # 5. Execution (Only if ALLOW)
        execution_result = {"status": "NOT_EXECUTED", "reason": "Execution blocked by preceding stages"}
        if guardrail_decision["status"] == "ALLOW":
            execution_result = self.executor.execute_action(
                event_id=event_id, 
                event_data=event_data, 
                action=guardrail_decision["action"], 
                guardrail_decision=guardrail_decision
            )
            log_audit_event(
                self.db, event_id, execution_result.get("attempt_id"), "ACTION_EXECUTION", 
                execution_result["status"], 
                execution_result.get("reason", ""),
                {"action": guardrail_decision["action"]}
            )
        elif guardrail_decision["status"] == "HUMAN_REVIEW":
            execution_result = {"status": "PENDING_HUMAN_REVIEW", "reason": guardrail_decision["reason"]}
            log_audit_event(
                self.db, event_id, None, "ACTION_BLOCKED", 
                "HUMAN_REVIEW", 
                guardrail_decision["reason"],
                {"action": guardrail_decision["action"]}
            )

        return {
            "ml_probability": ml_prediction["recovery_probability"],
            "llm_recommendation": llm_recommendation,
            "policy_decision": policy_decision,
            "guardrail_decision": guardrail_decision,
            "execution_result": execution_result
        }
