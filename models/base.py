from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/razorpay_recovery")

try:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    import logging
    logging.warning(f"Could not create database engine with {DATABASE_URL}: {e}. Falling back to sqlite memory db for tests.")
    from sqlalchemy.pool import StaticPool
    engine = create_engine('sqlite:///:memory:', connect_args={'check_same_thread': False}, poolclass=StaticPool)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    from sqlalchemy.ext.declarative import declarative_base
    Base = declarative_base()
    
    # We must delay the metadata create_all to after models are imported
    # but base doesn't know all models. We'll just let it fail or be empty if it's purely a web test.

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
