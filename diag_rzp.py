import os
import sys
from dotenv import load_dotenv
import razorpay

# Explicitly use the absolute path to the project root .env
project_root = r"c:\Users\KUMUD CHOUHAN\OneDrive\Desktop\razorpay buildathon"
env_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path=env_path, override=True)

key_id = os.environ.get('RAZORPAY_KEY_ID')
key_secret = os.environ.get('RAZORPAY_KEY_SECRET')

print("--- RAZORPAY DIAGNOSTIC ---")
print(f"ENV FILE PATH: {env_path}")
print(f"KEY PRESENT: {bool(key_id)}")
if key_id:
    print(f"KEY PREFIX: {key_id[:9]}")
    print(f"KEY LENGTH: {len(key_id)}")
else:
    print("KEY PREFIX: None")
    print("KEY LENGTH: None")

print(f"SECRET PRESENT: {bool(key_secret)}")
if key_secret:
    print(f"SECRET LENGTH: {len(key_secret)}")
else:
    print("SECRET LENGTH: None")
print("---------------------------")

if not key_id or not key_secret:
    print("ERROR: Missing credentials.")
    sys.exit(1)

try:
    print("\nInitializing Razorpay SDK and testing authentication...")
    client = razorpay.Client(auth=(key_id, key_secret))
    # Safe read
    res = client.order.all({'count': 1})
    print("PASS: Razorpay Test Authentication Succeeded.")
except razorpay.errors.BadRequestError as e:
    print(f"FAILED (BadRequestError): {str(e)}")
    sys.exit(1)
except Exception as e:
    print(f"FAILED: {str(e)}")
    sys.exit(1)
