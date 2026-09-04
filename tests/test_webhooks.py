import time
import hmac
import hashlib
import os
import json
import uuid
import unittest
from fastapi.testclient import TestClient

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app
from models.base import Base, engine
import models.core 
from unittest.mock import patch

def sign_payload(payload: dict, secret: str) -> tuple:
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    sig = hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()
    return payload_bytes, sig

class TestWebhooks(unittest.TestCase):
    def setUp(self):
        if engine:
            Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)
        self.secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "webhook_secret")
        
        self.patcher = patch('api.webhooks.process_razorpay_event')
        self.mock_process = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        if engine:
            Base.metadata.drop_all(bind=engine)

    def test_webhook_valid_signature_payment_failed(self):
        payload = {
            "account_id": "acc_123",
            "event": "payment.failed",
            "payload": {
                "payment": {
                    "entity": {
                        "id": f"pay_{uuid.uuid4()}",
                        "amount": 1000,
                        "currency": "INR",
                        "error_code": "issuer_down"
                    }
                }
            },
            "created_at": 1234567890
        }
        body, sig = sign_payload(payload, self.secret)
        
        start_time = time.time()
        response = self.client.post("/webhooks/razorpay", content=body, headers={"x-razorpay-signature": sig})
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "message": "event queued"})
        self.assertTrue((end_time - start_time) < 0.5)

    def test_webhook_missing_signature(self):
        payload = b'{"account_id": "acc_123", "event":"payment.failed"}'
        response = self.client.post("/webhooks/razorpay", content=payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json(), {"detail": "Invalid signature"})

    def test_webhook_invalid_signature(self):
        payload = b'{"account_id": "acc_123", "event":"payment.failed"}'
        response = self.client.post("/webhooks/razorpay", content=payload, headers={"x-razorpay-signature": "bad_sig"})
        self.assertEqual(response.status_code, 400)

    def test_webhook_unsupported_event(self):
        payload = {"account_id": "acc_123", "created_at": 1234567890, "event": "invoice.paid", "payload": {}}
        body, sig = sign_payload(payload, self.secret)
        
        response = self.client.post("/webhooks/razorpay", content=body, headers={"x-razorpay-signature": sig})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ignored", "reason": "unsupported event type"})

    def test_webhook_payment_authorized_captured(self):
        for evt in ["payment.authorized", "payment.captured"]:
            payload = {"account_id": "acc_123", "created_at": 1234567890, "event": evt, "payload": {"payment": {"entity": {"id": f"pay_{uuid.uuid4()}"}}}}
            body, sig = sign_payload(payload, self.secret)
            response = self.client.post("/webhooks/razorpay", content=body, headers={"x-razorpay-signature": sig})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {"status": "ok", "message": "event queued"})

    def test_webhook_duplicate_event_idempotency(self):
        event_id = f"evt_{uuid.uuid4()}"
        payload = {
            "account_id": "acc_123",
            "created_at": 1234567890,
            "event": "payment.failed",
            "payload": {
                "id": event_id,
                "payment": {
                    "entity": {
                        "id": f"pay_{uuid.uuid4()}",
                        "amount": 1000
                    }
                }
            }
        }
        body, sig = sign_payload(payload, self.secret)
        
        r1 = self.client.post("/webhooks/razorpay", content=body, headers={"x-razorpay-signature": sig})
        r2 = self.client.post("/webhooks/razorpay", content=body, headers={"x-razorpay-signature": sig})
        
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r2.status_code, 200)

if __name__ == '__main__':
    unittest.main()
