# Phase 1: ML Data + Feature Engineering

This module provides the data foundation for predicting recovery probability for failed transactions in ReviveAI.

**IMPORTANT: ML model training and inference are NOT implemented in this phase.**

## 1. ML Problem Definition
The problem is formulated as a binary classification task. For a given recovery opportunity (a failed transaction or subscription), the goal is to predict the probability that a recovery intervention will be successful.

## 2. Prediction Target
- **Target Variable**: `recovered` (Binary: 1 for successful recovery, 0 for failure).
- **Definition**: A success is defined as the customer fulfilling the payment within the observation window following the intervention. A failure is defined as no successful payment within that window.

## 3. Feature Groups
Features are divided into four main groups:
- **Transaction Features**: `amount`, `currency`, `payment_method`, `transaction_hour`, `transaction_day`, `amount_relative_to_customer_average`.
- **Failure Features**: `error_code`, `root_cause_diagnosis`, `previous_failure_count`.
- **Customer Behavior**: `total_previous_payments`, `successful_payments`, `failed_payments`, `historical_success_rate`, `customer_tenure`, `average_transaction_amount`.
- **Recovery History**: `previous_intervention_count`, `previous_successful_recoveries`, `historical_recovery_rate`, `time_since_last_intervention`.
- **Subscription Features**: `subscription_status`, `previous_subscription_failures`.

## 4. Label Definition
The label `recovered` is derived by inspecting the state of the `RecoveryOutcome` at the end of a predefined observation window (e.g., 24 hours after intervention).

## 5. Synthetic Data Generation
`ml/data/generate_dataset.py` generates a flattened, analytical Pandas DataFrame simulating realistic data distributions and correlations. It introduces logical noise to avoid perfect determinism, ensuring that concepts like "transient failures have higher recovery rates" hold true probabilistically.

## 6. Feature Engineering
`ml/features.py` defines a reproducible Scikit-Learn `ColumnTransformer` pipeline. It handles:
- **Missing values**: Median imputation for numerics, constant 'missing' for categoricals.
- **Scaling**: Standard scaling for numeric features.
- **Encoding**: One-hot encoding for categorical features.

## 7. Leakage Prevention
Strict target leakage rules are enforced:
- Future information (e.g., `amount_recovered`) is explicitly excluded.
- The `ColumnTransformer` specifies exactly which columns are permitted; any extra columns are dropped (`remainder='drop'`).
- Time-aware dataset splitting ensures future data does not leak into the training set.

## 8. Dataset Splitting
`ml/dataset.py` implements a time-based split sorting by `intervention_timestamp` to simulate real-world streaming deployments (Train -> Val -> Test chronologically).

## 9. Baseline
`ml/baseline.py` implements two baseline predictors:
- **Overall Baseline**: Predicts the global historical recovery mean.
- **Category Baseline**: Predicts the historical mean for a specific `root_cause_diagnosis`.

These baselines serve as the benchmark for future ML models.

## 10. Future ML Model Integration
In Phase 2, a predictive model (e.g., XGBoost, LightGBM) will consume the pipeline output from `features.py` and output a probability score that will inform the LLM Agent's recovery orchestration.
