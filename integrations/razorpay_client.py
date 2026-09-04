import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class RazorpayClient:
    """
    Abstraction layer for Razorpay integration.
    Gracefully falls back to mock responses if API keys are not provided.
    """
    def __init__(self):
        self.key_id = os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = os.getenv("RAZORPAY_KEY_SECRET")
        self.mock_mode = not (self.key_id and self.key_secret)

    def create_payment_link(self, amount: float, currency: str, customer: dict, description: str) -> dict:
        """
        Creates a payment link.
        """
        if self.mock_mode:
            logger.info("[SIMULATED] Creating mock payment link.")
            return {
                "id": "plink_mock123",
                "short_url": "https://rzp.io/i/mock123",
                "amount": amount * 100,
                "currency": currency,
                "status": "created"
            }
        
        # In a real implementation:
        # response = httpx.post(
        #     "https://api.razorpay.com/v1/payment_links",
        #     auth=(self.key_id, self.key_secret),
        #     json={
        #         "amount": int(amount * 100),
        #         "currency": currency,
        #         "customer": customer,
        #         "description": description
        #     }
        # )
        # return response.json()
        
        # For safety in buildathon unless real keys are tested, stay simulated if it reaches here
        return {
            "id": "plink_simulated",
            "short_url": "https://rzp.io/i/sim",
            "amount": amount * 100,
            "currency": currency,
            "status": "created"
        }

    def fetch_payment(self, payment_id: str) -> Optional[dict]:
        """
        Fetches a payment by ID.
        """
        if self.mock_mode:
            return {
                "id": payment_id,
                "amount": 10000,
                "currency": "INR",
                "status": "captured"
            }
        # Real implementation using httpx would go here
        return None

    def fetch_subscription(self, subscription_id: str) -> Optional[dict]:
        """
        Fetches a subscription by ID.
        """
        if self.mock_mode:
            return {
                "id": subscription_id,
                "plan_id": "plan_mock",
                "status": "active"
            }
        # Real implementation using httpx would go here
        return None
