from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import Base

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    dnd = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey('customers.id'))
    amount = Column(Float)
    currency = Column(String, default='INR')
    status = Column(String)
    method = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column(String, primary_key=True, index=True)
    customer_id = Column(String, ForeignKey('customers.id'))
    plan_id = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class PaymentEvent(Base):
    __tablename__ = 'payment_events'
    id = Column(String, primary_key=True, index=True)
    event_type = Column(String)
    customer_id = Column(String, ForeignKey('customers.id'), nullable=True)
    payment_id = Column(String, ForeignKey('payments.id'), nullable=True)
    subscription_id = Column(String, ForeignKey('subscriptions.id'), nullable=True)
    error_code = Column(String, nullable=True)
    payload = Column(JSON)
    processed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class RecoveryPolicy(Base):
    __tablename__ = 'recovery_policies'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    root_cause = Column(String, unique=True)
    actions = Column(JSON) # e.g. ["retry_payment", "send_link"]
    max_attempts = Column(Integer)
    cooldown_hours = Column(JSON) # e.g. [1, 6, 24]

class RecoveryAttempt(Base):
    __tablename__ = 'recovery_attempts'
    id = Column(String, primary_key=True, index=True)
    event_id = Column(String, ForeignKey('payment_events.id'))
    action = Column(String)
    status = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class RecoveryOutcome(Base):
    __tablename__ = 'recovery_outcomes'
    id = Column(String, primary_key=True, index=True)
    event_id = Column(String, ForeignKey('payment_events.id'))
    amount_at_risk = Column(Float)
    amount_recovered = Column(Float, default=0.0)
    status = Column(String)
    recovered_at = Column(DateTime, nullable=True)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(String, nullable=True)
    reference_id = Column(String, nullable=True)
    action_type = Column(String)
    decision = Column(String)
    reasoning = Column(String)
    metadata_ = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
