# Model Card: Recovery Probability Model

## Model Objective
Predict the probability of a successful recovery (P(recovered = 1)) following an intervention for a failed payment or subscription.

## Target Definition
- **recovered**: 1 if the payment is successfully captured within the observation window, 0 otherwise.

## Dataset Description
- **Source**: Synthetic dataset representing historical recovery opportunities (`ml/data/synthetic_recovery_data.csv`).
- **Nature**: Highly imbalanced (22.86% recovery rate).
- **Rows**: 20,000
- **Features**: 21
- **Split**: Chronological (Train: 14,000 | Validation: 3,000 | Test: 3,000).

## Feature Groups
- Transaction Features (amount, currency, etc.)
- Failure Features (root cause, error code)
- Customer Behavior (history, tenure)
- Recovery History (past interventions)
- Subscription Features (status, failures)

## Training Methodology
- **Preprocessing**: Median imputation for numerics, constant imputation and one-hot encoding for categoricals, followed by standard scaling. Fit exclusively on the training set.
- **Candidate Models**: Logistic Regression (Model A) and HistGradientBoostingClassifier (Model B).
- **Model Selection**: Conducted based on Validation set PR-AUC and business metric ranking capabilities. Test data was strictly held out until final evaluation.

## Baselines
- **Global**: 22.86% probability assignment to all instances.
- **Category**: Based on `root_cause_diagnosis`.

## Validation Metrics
- **Logistic Regression**: ROC-AUC: 0.7326 | PR-AUC: 0.3998 | Brier Score: 0.2116
- **HistGradientBoosting**: ROC-AUC: 0.7413 | PR-AUC: 0.4102 | Brier Score: 0.1559

## Final Test Metrics (HistGradientBoosting)
- **ROC-AUC**: 0.7558
- **PR-AUC**: 0.4303
- **Log Loss**: 0.4707
- **Precision**: 0.3571
- **Recall**: 0.0140
- **F1**: 0.0270
- **Brier Score**: 0.1546

## Business Metrics on Test Set (HistGradientBoosting)
- **Top 10%**: 300 opportunities | $301k at risk | $162k recovered | 47.00% recovery rate | 46.12% avg pred prob
- **Top 20%**: 600 opportunities | $647k at risk | $331k recovered | 47.83% recovery rate | 44.13% avg pred prob
- **Top 30%**: 900 opportunities | $1.01m at risk | $484k recovered | 46.11% recovery rate | 42.24% avg pred prob
- **Top 50%**: 1500 opportunities | $2.01m at risk | $748k recovered | 38.93% recovery rate | 36.88% avg pred prob

## Top 10 Predictive Features
1. `amount_relative_to_customer_average` (important for prediction)
2. `historical_recovery_rate` (important for prediction)
3. `customer_tenure` (important for prediction)
4. `previous_failure_count` (important for prediction)
5. `error_code_issuer_down` (important for prediction)
6. `total_previous_payments` (important for prediction)
7. `failed_payments` (important for prediction)
8. `payment_method_upi` (important for prediction)
9. `transaction_day` (important for prediction)
10. `error_code_network_error` (important for prediction)

## Selected Model
- **Algorithm**: HistGradientBoostingClassifier
- **Rationale**: HistGradientBoosting demonstrated superior PR-AUC (0.4102 vs 0.3998) and substantially better calibration/Brier Score (0.1559 vs 0.2116) on the validation set. It is capable of capturing non-linear interactions natively and outperforms the simple category baseline by yielding $162k recovered in the Top 10% vs the Baseline's $135k.

## Limitations & Risks
- **Synthetic Data Limit**: The dataset is completely synthetic and these metrics do not represent production merchant performance. High or low performance is a direct result of the simulation logic and noise parameters. The recall is noticeably low at the default 0.5 threshold due to the imbalanced nature and probability distribution clamping during dataset generation.
- **Real-World Requirement**: For production, this model must be retrained on actual Razorpay webhook historical events and recovery outcomes.

## Artifacts
- `ml/models/recovery_model.pkl`: The serialized classifier.
- `ml/models/preprocessor.pkl`: The serialized feature pipeline.
