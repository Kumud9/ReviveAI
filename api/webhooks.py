from fastapi import APIRouter, Request, Header, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import os
import hmac
import hashlib
from typing import Optional

from models.base import SessionLocal
from schemas.events import RazorpayWebhookEvent
from services.event_processor import process_razorpay_event

router = APIRouter()

WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "webhook_secret")
ALLOWED_EVENTS = {"payment.failed", "payment.authorized", "payment.captured"}

def verify_signature(payload_body: bytes, signature: str) -> bool:
    if not signature:
        return False
    expected_signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_signature, signature)

def background_process_event(event_data: dict):
    db = SessionLocal()
    try:
        event = RazorpayWebhookEvent(**event_data)
        process_razorpay_event(event, db)
    finally:
        db.close()

@router.post("/razorpay")
async def razorpay_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_razorpay_signature: Optional[str] = Header(None)
):
    payload_body = await request.body()
    
    # 1. Signature Validation
    if not verify_signature(payload_body, x_razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    try:
        payload = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event_type = payload.get("event")
    
    # 2. Event Filtering
    if event_type not in ALLOWED_EVENTS:
        # Return success safely without processing unsupported events
        return {"status": "ignored", "reason": "unsupported event type"}

    # 3. Async Processing
    background_tasks.add_task(background_process_event, payload)
    
    return {"status": "ok", "message": "event queued"}
