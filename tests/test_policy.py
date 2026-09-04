from engines.policy import get_policy_for_diagnosis
from models.base import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

def test_get_policy_transient(db_session):
    policy = get_policy_for_diagnosis("TRANSIENT", db_session)
    assert policy["max_attempts"] == 3
    assert "retry_payment" in policy["actions"]

def test_get_policy_hard_decline(db_session):
    policy = get_policy_for_diagnosis("HARD_DECLINE", db_session)
    assert policy["max_attempts"] == 2
    assert "send_payment_update_link" in policy["actions"]
