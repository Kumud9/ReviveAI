# ReviveAI

**Autonomous, AI-driven revenue recovery agent for failed payments.**

ReviveAI is an intelligent agentic system that automatically diagnoses failed payments, formulates a recovery strategy using LLMs and Machine Learning, evaluates decisions against strict safety guardrails, and executes Razorpay recovery actions—all without human intervention.

---

## 🎯 The Problem

When a payment fails, merchants lose immediate revenue and risk permanent customer churn. Traditional retries are often blind (re-attempting without context), static (relying on basic rules rather than intent), and risky (potentially violating payment network rules or causing double-charges). Most companies lack the capability to analyze exactly *why* a payment failed and determine the safest, most statistically likely way to recover it in real-time.

## 💡 The Solution

ReviveAI listens to real-time Razorpay webhooks. It uses a custom Machine Learning model to score the probability of recovery and an LLM to contextually diagnose the exact error reason. Before any action is taken, deterministic policies and strict safety guardrails ensure compliance. Finally, it executes the optimal recovery action via the Razorpay API.

## ✨ Key Features

- **Real-time Webhook Ingestion:** Securely processes `payment.failed` events.
- **ML Scoring:** Predicts the likelihood of successful recovery based on historical features.
- **LLM Investigation:** Deeply analyzes failure reasons (e.g., `BAD_REQUEST_ERROR`, `INSUFFICIENT_FUNDS`) to classify them.
- **Policy Engine:** Maps diagnoses to optimal recovery actions (e.g., generate a payment link, programmatic retry, or gracefully drop).
- **Safety Guardrails:** Hardcoded checks ensure the LLM cannot hallucinate dangerous actions, preventing double charges or immediate blind retries.
- **Idempotency & Audit Trails:** Complete, immutable logs of every AI decision and action to ensure no duplicate processing.
- **Premium Frontend:** A dark-themed, responsive dashboard providing complete visibility into the AI's operations.

---

## 🔄 How ReviveAI Works

1. **Razorpay Webhook:** A `payment.failed` event is securely ingested and its HMAC signature is verified.
2. **ML Scoring:** The system calculates the probability of recovery using a trained ML model.
3. **LLM Investigation:** An LLM analyzes the error payload to diagnose the root cause (e.g., Transient vs. Terminal error).
4. **Policy Engine:** Selects the best recovery action based on the diagnosis.
5. **Guardrails:** Evaluates the proposed action against strict safety limits (e.g., timeout rules, action validity).
6. **Execution:** The Executor communicates with the Razorpay API (Test Mode) to perform the action.
7. **Outcome Tracking:** Logs the execution state and tracks the amount at risk.
8. **Analytics:** Activity is surfaced to the frontend dashboard.

## 🏗 Architecture

```mermaid
flowchart TD
    A[Razorpay Webhook] -->|payment.failed| B(Webhook Signature Verification)
    B --> C{Idempotency Check}
    C -- Exists --> D[Drop Event]
    C -- New --> E[PostgreSQL Event Store]
    
    E --> F[ML Scoring Engine]
    F --> G[LLM Investigator]
    G --> H[Policy Engine]
    H --> I{Safety Guardrails}
    
    I -- Blocked --> J[Log Failure & Halt]
    I -- Approved --> K[Executor]
    
    K --> L((Razorpay API))
    K --> M[Outcome Tracker & Audit Log]
    M --> N[Frontend Dashboard]
```

## 🛠 Tech Stack

| Domain | Technology |
|---|---|
| **Backend** | Python, FastAPI, SQLAlchemy |
| **Database** | PostgreSQL (Dockerized) / SQLite fallback |
| **AI / ML** | Scikit-Learn (RandomForest), LLM Integration |
| **Frontend** | React, Vite, Tailwind CSS (v4), shadcn/ui, Recharts |
| **Integration** | Razorpay Python SDK |

---

## 🧠 ML Approach & LLM Role

### Machine Learning
The ML component is currently trained on **synthetic data** to simulate historical payment patterns. It uses a Random Forest classifier to generate a probability score for recovery success based on features like amount, currency, and error source. Current validation metrics reflect performance on this synthetic dataset and are used to inform the AI rather than make definitive financial choices.

### The Role of the LLM
The LLM is strictly an **investigator**. It receives the error payload and context to provide a human-readable diagnosis and categorization (e.g., classifying an error as transient network failure vs. hard decline). 

**Crucially, the LLM cannot directly execute actions.** Its output is piped through a deterministic **Policy Engine** and evaluated by strict **Safety Guardrails**. This prevents AI hallucinations from causing accidental financial transactions or infinite retry loops.

---

## 🔒 Safety, Idempotency, and Auditing

- **Webhook HMAC Verification:** Ensures all incoming events genuinely originated from Razorpay.
- **Idempotency:** Webhook IDs are tracked in the database. Duplicate webhooks are successfully intercepted and ignored.
- **Audit Trail:** Every stage—from ingestion to execution—is logged immutably.
- **Guardrails:** Deterministic functions that veto any unsafe action proposed by the policy layer.

---

## 💳 Razorpay Test Mode Integration

ReviveAI is built and verified entirely using **Razorpay Test Mode**. No real money is moved.
Actions such as `retry_payment` or generating `payment_links` are executed against the Razorpay Test API. 

*(Note: The system correctly identifies that standard one-time payments without tokens/mandates cannot be programmatically retried via API. It elegantly handles this by marking the execution status as `NOT_EXECUTABLE` rather than faking success).*

---

## 🚀 Local Setup & Run Commands

### Prerequisites
- Python 3.10+
- Node.js & npm
- Docker (optional, for PostgreSQL)

### 1. Environment Variables
Create a `.env` file in the project root:
```env
# Razorpay Credentials (Test Mode Only)
RAZORPAY_KEY_ID=rzp_test_placeholder
RAZORPAY_KEY_SECRET=placeholder_secret
RAZORPAY_WEBHOOK_SECRET=placeholder_webhook_secret

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# LLM 
LLM_API_KEY=placeholder_api_key
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/Scripts/activate # Windows

# Install dependencies
pip install -r requirements.txt

# Start backend server
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## 📡 API & Webhooks

- `POST /webhooks/razorpay`: The primary ingestion endpoint for Razorpay webhooks.
- `GET /health`: Health check endpoint.

## 🧪 Testing

The system includes end-to-end tests verifying the entire lifecycle.
```bash
# Run end-to-end integration test
python test_e2e_phase6.py
```

## 🚧 Current Limitations & Honest Status

- **Programmatic Retries:** Standard one-time payments generally require customer intervention (e.g., 3DS). The system currently logs these as `NOT_EXECUTABLE` rather than forcefully bypassing rules.
- **ML Evaluation:** The ML model metrics are based on synthetically generated data for the purpose of the buildathon.
- **Current Status:** The core backend pipeline (Webhook → ML → LLM → Policy → Guardrails → Executor → Razorpay Test API) is fully integrated and tested. The frontend is scaffolded structurally but is pending API connection.

## 🔮 Future Improvements

- Fully connect the React frontend to the backend REST APIs.
- Incorporate Razorpay Webhook `payment_link.paid` events to close the loop on actual recovery amounts.
- Fine-tune the ML model on real (anonymized) historical merchant data.
- Add support for subscription/mandate-based automated retries.

---

## 📄 License

MIT License.
