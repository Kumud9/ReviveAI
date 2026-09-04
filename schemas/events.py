from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class RazorpayWebhookEvent(BaseModel):
    event: str
    account_id: str
    payload: Dict[str, Any]
    created_at: int

class PaymentEventSchema(BaseModel):
    id: str
    event_type: str
    customer_id: Optional[str] = None
    payment_id: Optional[str] = None
    subscription_id: Optional[str] = None
    amount: float
    currency: str = "INR"
    error_code: Optional[str] = None
    payload: Dict[str, Any]
    timestamp: datetime
