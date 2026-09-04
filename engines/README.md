# ReviveAI Engines & Orchestration

This module contains the deterministic Policy Engine, fail-closed Guardrails, and Orchestrator for Phase 4 execution.

## Policy Engine (`engines/recovery_policy.py`)
Applies deterministic rules to an LLM recommendation to ensure business logic compliance.
- **Max attempts:** Blocks action if attempt limits are exceeded.
- **Cooldown:** Enforces cooldowns between attempts to prevent spam.
- **Amount thresholds:** Escalates high-value transactions to human review.
- **Confidence bounds:** Enforces a minimum confidence threshold on LLM output.

## Guardrails (`engines/recovery_guardrails.py`)
Acts as the final, strict gatekeeper prior to Execution.
- Fails closed upon any invalid inputs.
- Validates the action exists in explicitly permitted sets.
- Asserts the amount is positive.
- Asserts that a duplicate idempotency collision does not exist (no pending actions).

## Executor (`services/executor.py`)
The executor receives authorized instructions.
- It will **ONLY** execute if `Guardrails` explicitly pass an `ALLOW` status.
- Implements `NOT_EXECUTABLE` statuses for actions that the current Razorpay implementation cannot safely process (e.g. forced retry payments).
- Implements Razorpay test-mode API integration explicitly bounded by TEST keys (`rzp_test_`).

## Orchestrator (`services/orchestrator.py`)
Connects the data flow linearly:
`ML -> LLM -> Policy -> Guardrails -> Executor`

## Idempotency
Checked at both the Guardrail layer (blocking duplicates in progress) and the Executor layer (deduplicating rapid identical requests), enforcing safe, once-and-only-once semantics.

## Audit Trail
`services/audit.py` records append-only logs for Policy decisions, Guardrail decisions, and Executor status. 
*No PII or secrets are logged.*
