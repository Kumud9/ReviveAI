from fastapi import FastAPI
from fastapi.responses import JSONResponse
from api.webhooks import router as webhooks_router
import os
from dotenv import load_dotenv

# Ensure root .env is loaded (overriding appropriately if needed)
load_dotenv(override=True)

app = FastAPI(
    title="Razorpay Revenue Recovery Agent",
    description="Agentic system to recover revenue from failed payments, abandoned checkouts, and failed subscriptions.",
    version="1.0.0"
)

app.include_router(webhooks_router, prefix="/webhooks", tags=["Webhooks"])

@app.get("/health")
async def health_check():
    return JSONResponse(content={"status": "ok", "message": "Revenue Recovery Agent is running."})
