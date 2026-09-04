import os
import pickle
import pandas as pd
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score, average_precision_score, log_loss, precision_score, recall_score, f1_score, brier_score_loss, confusion_matrix
import sys

# Ensure we can import from the ml directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from dataset import prepare_ml_data
from features import engineer_features
from baseline import BaselineModel

def evaluate_model(model, X, y, threshold=0.5):
    preds_proba = model.predict_proba(X)[:, 1]
    preds = (preds_proba >= threshold).astype(int)
    
    metrics = {
        "ROC-AUC": roc_auc_score(y, preds_proba),
        "PR-AUC": average_precision_score(y, preds_proba),
        "Log Loss": log_loss(y, preds_proba),
        "Precision": precision_score(y, preds),
        "Recall": recall_score(y, preds),
        "F1": f1_score(y, preds),
        "Brier Score": brier_score_loss(y, preds_proba)
    }
    cm = confusion_matrix(y, preds)
    return metrics, cm, preds_proba

def evaluate_business_metrics(y_true, preds_proba, amounts):
    """
    Evaluates how well the model concentrates recoverable revenue in the top percentiles.
    """
    df = pd.DataFrame({
        'y_true': y_true,
        'pred_prob': preds_proba,
        'amount': amounts
    })
    
    df = df.sort_values('pred_prob', ascending=False).reset_index(drop=True)
    n = len(df)
    
    results = {}
    for pct in [0.1, 0.2, 0.3, 0.5]:
        cutoff = int(n * pct)
        top_df = df.iloc[:cutoff]
        
        results[f"Top {int(pct*100)}%"] = {
            "opportunities": cutoff,
            "revenue_at_risk": top_df['amount'].sum(),
            "actual_recovered_revenue": top_df[top_df['y_true'] == 1]['amount'].sum(),
            "recovery_rate": top_df['y_true'].mean(),
            "expected_recovery_value": (top_df['amount'] * top_df['pred_prob']).sum(),
            "avg_pred_prob": top_df['pred_prob'].mean()
        }
    return results

def main():
    print("Loading dataset and splitting...")
    train_df, val_df, test_df, y_train, y_val, y_test = prepare_ml_data("ml/data/synthetic_recovery_data.csv")
    
    print("Applying feature engineering pipeline...")
    # Fit on train ONLY
    X_train, preprocessor = engineer_features(train_df.drop(columns=['recovered', 'intervention_timestamp']), fit=True)
    
    # Transform val and test
    X_val, _ = engineer_features(val_df.drop(columns=['recovered', 'intervention_timestamp']), fit=False, preprocessor=preprocessor)
    X_test, _ = engineer_features(test_df.drop(columns=['recovered', 'intervention_timestamp']), fit=False, preprocessor=preprocessor)
    
    print(f"X_train shape: {X_train.shape}")
    
    # Baseline for comparison
    baseline = BaselineModel()
    baseline.fit(train_df, y_train)
    val_baseline_preds = baseline.predict_proba_category(val_df)
    
    print("\n--- Training Model A: Logistic Regression ---")
    model_a = LogisticRegression(max_iter=1000, random_state=42, class_weight='balanced')
    model_a.fit(X_train, y_train)
    
    print("\n--- Training Model B: HistGradientBoostingClassifier ---")
    model_b = HistGradientBoostingClassifier(random_state=42, max_iter=200, learning_rate=0.05)
    model_b.fit(X_train, y_train)
    
    print("\n--- Validation Evaluation ---")
    metrics_a, cm_a, proba_a = evaluate_model(model_a, X_val, y_val)
    metrics_b, cm_b, proba_b = evaluate_model(model_b, X_val, y_val)
    
    print(f"Logistic Regression ROC-AUC: {metrics_a['ROC-AUC']:.4f}")
    print(f"Gradient Boosting ROC-AUC:   {metrics_b['ROC-AUC']:.4f}")
    
    print(f"Logistic Regression PR-AUC:  {metrics_a['PR-AUC']:.4f}")
    print(f"Gradient Boosting PR-AUC:    {metrics_b['PR-AUC']:.4f}")
    
    print(f"Logistic Regression Brier:   {metrics_a['Brier Score']:.4f}")
    print(f"Gradient Boosting Brier:     {metrics_b['Brier Score']:.4f}")
    
    # Selection logic: we choose Model B because tree-based models generally capture non-linear relations better 
    # and we don't need strict linearity for this business usecase.
    print("\n--- Model Selection ---")
    selected_model = model_b
    model_name = "HistGradientBoostingClassifier"
    print(f"Selected Model: {model_name} due to typically better ranking/PR-AUC capabilities and lack of linearity assumptions.")
    
    print("\n--- Test Set Evaluation (Final) ---")
    metrics_test, cm_test, proba_test = evaluate_model(selected_model, X_test, y_test)
    for k, v in metrics_test.items():
        print(f"{k}: {v:.4f}")
    
    print("\n--- Business Metrics on Test Set ---")
    amounts_test = test_df['amount'].values
    biz_metrics = evaluate_business_metrics(y_test, proba_test, amounts_test)
    
    for bucket, data in biz_metrics.items():
        print(f"\n{bucket}:")
        for k, v in data.items():
            if 'revenue' in k or 'value' in k:
                print(f"  {k}: {v:.2f}")
            elif 'rate' in k or 'prob' in k:
                print(f"  {k}: {v:.2%}")
            else:
                print(f"  {k}: {v}")
                
    # Evaluate Baseline Business Metrics on Test Set for comparison
    test_baseline_preds = baseline.predict_proba_category(test_df)
    biz_metrics_baseline = evaluate_business_metrics(y_test, test_baseline_preds, amounts_test)
    
    print("\n--- Baseline Business Metrics (Failure-Category) on Test Set ---")
    print(f"Top 10% Actual Recovered Revenue (Baseline): {biz_metrics_baseline['Top 10%']['actual_recovered_revenue']:.2f}")
    print(f"Top 10% Actual Recovered Revenue (ML Model): {biz_metrics['Top 10%']['actual_recovered_revenue']:.2f}")
                
    print("\n--- Saving Artifacts ---")
    os.makedirs("ml/models", exist_ok=True)
    with open("ml/models/preprocessor.pkl", "wb") as f:
        pickle.dump(preprocessor, f)
    with open("ml/models/recovery_model.pkl", "wb") as f:
        pickle.dump(selected_model, f)
    print("Saved to ml/models/preprocessor.pkl and ml/models/recovery_model.pkl")

if __name__ == "__main__":
    main()
