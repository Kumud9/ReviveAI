from integrations.razorpay_client import RazorpayClient
import os

def test_razorpay_client_mock_mode_payment_link():
    # Force mock mode
    os.environ.pop("RAZORPAY_KEY_ID", None)
    os.environ.pop("RAZORPAY_KEY_SECRET", None)
    
    client = RazorpayClient()
    assert client.mock_mode is True
    
    response = client.create_payment_link(100.0, "INR", {"email": "test@example.com"}, "test")
    assert response["status"] == "created"
    assert response["amount"] == 10000

def test_razorpay_client_mock_mode_fetch():
    os.environ.pop("RAZORPAY_KEY_ID", None)
    os.environ.pop("RAZORPAY_KEY_SECRET", None)
    
    client = RazorpayClient()
    response = client.fetch_payment("pay_123")
    assert response["id"] == "pay_123"
    assert response["status"] == "captured"
