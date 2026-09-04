import pandas as pd
import numpy as np

class BaselineModel:
    """
    Implements two baselines:
    1. Overall historical recovery rate (predicts the global mean for everyone).
    2. Failure-category recovery rate (predicts the mean recovery rate for that specific root cause).
    """
    def __init__(self):
        self.global_rate = 0.0
        self.category_rates = {}
        
    def fit(self, X_train: pd.DataFrame, y_train: pd.Series):
        """
        Calculates baseline rates using ONLY the training set to avoid leakage.
        """
        # 1. Overall baseline
        self.global_rate = y_train.mean()
        
        # 2. Category baseline
        # We assume X_train has the raw categorical 'root_cause_diagnosis' column
        if 'root_cause_diagnosis' in X_train.columns:
            # Combine X and y temporarily
            df = X_train.copy()
            df['target'] = y_train
            self.category_rates = df.groupby('root_cause_diagnosis')['target'].mean().to_dict()
        else:
            print("Warning: 'root_cause_diagnosis' not found. Category baseline will fall back to global.")
            
    def predict_proba_overall(self, X_test: pd.DataFrame):
        """Returns the global mean for all rows."""
        return np.full(len(X_test), self.global_rate)
        
    def predict_proba_category(self, X_test: pd.DataFrame):
        """Returns the mean for the specific category, falling back to global mean if unknown."""
        if 'root_cause_diagnosis' in X_test.columns:
            return X_test['root_cause_diagnosis'].map(self.category_rates).fillna(self.global_rate).values
        else:
            return self.predict_proba_overall(X_test)

if __name__ == "__main__":
    from dataset import prepare_ml_data
    from sklearn.metrics import roc_auc_score, log_loss
    import os
    
    if os.path.exists("synthetic_recovery_data.csv"):
        train_df, val_df, test_df, y_train, y_val, y_test = prepare_ml_data("synthetic_recovery_data.csv")
        
        baseline = BaselineModel()
        baseline.fit(train_df, y_train)
        
        preds_overall = baseline.predict_proba_overall(test_df)
        preds_cat = baseline.predict_proba_category(test_df)
        
        print(f"Global Baseline Recovery Rate: {baseline.global_rate:.2%}")
        print("Category Baseline Rates:")
        for k, v in baseline.category_rates.items():
            print(f"  {k}: {v:.2%}")
            
        print("\nTest Set Evaluation:")
        print(f"Overall Baseline ROC AUC: {roc_auc_score(y_test, preds_overall):.4f} (Expected 0.5 for constant)")
        print(f"Category Baseline ROC AUC: {roc_auc_score(y_test, preds_cat):.4f}")
        
        print(f"Overall Baseline Log Loss: {log_loss(y_test, preds_overall):.4f}")
        print(f"Category Baseline Log Loss: {log_loss(y_test, preds_cat):.4f}")
