import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text
from models.base import SessionLocal, engine

# Ensure root .env is loaded
project_root = r"c:\Users\KUMUD CHOUHAN\OneDrive\Desktop\razorpay buildathon"
env_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path=env_path, override=True)

db_url = os.environ.get("DATABASE_URL")
if not db_url:
    print("DATABASE_URL not found in environment.")
    sys.exit(1)

# Mask the password for reporting
try:
    prefix = db_url.split("://")[0] + "://"
    user_pass, host_path = db_url.split("://")[1].split("@")
    user, _ = user_pass.split(":")
    masked_db_url = f"{prefix}{user}:<PASSWORD>@{host_path}"
except Exception:
    masked_db_url = "<UNPARSEABLE_DB_URL>"

print("--- DATABASE DIAGNOSTIC ---")
print(f"ENV FILE PATH: {env_path}")
print(f"DATABASE_URL (masked): {masked_db_url}")
print(f"Engine Dialect: {engine.name}")

sqlite_fallback_active = (engine.name == 'sqlite')
print(f"SQLite Fallback Active: {sqlite_fallback_active}")

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        val = result.scalar()
        print(f"Connection Test: PASS (SELECT 1 returned {val})")
except Exception as e:
    print(f"Connection Test: FAIL ({str(e)})")
