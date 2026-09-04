from sqlalchemy.orm import Session
from models.core import AuditLog
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

def log_audit_event(
    db: Session,
    event_id: Optional[str],
    reference_id: Optional[str],
    action_type: str,
    decision: str,
    reasoning: str,
    metadata_: Optional[Dict[str, Any]] = None
):
    """
    Append-only audit log writer.
    """
    audit_entry = AuditLog(
        event_id=event_id,
        reference_id=reference_id,
        action_type=action_type,
        decision=decision,
        reasoning=reasoning,
        metadata_=metadata_ or {}
    )
    db.add(audit_entry)
    # Commit immediately to ensure audit trace is persisted even if later steps fail.
    # In a real high-throughput system, this might use a separate connection or async queue.
    db.commit()
    
    logger.info(f"AUDIT | {action_type} | {decision} | {reasoning}")
