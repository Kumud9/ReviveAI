import pickle
import pandas as pd
import sys
from sklearn.inspection import permutation_importance

sys.path.append('.')
from ml.dataset import prepare_ml_data
from ml.features import engineer_features

def main():
    train_df, val_df, test_df, yt, yv, ytst = prepare_ml_data('ml/data/synthetic_recovery_data.csv')
    with open('ml/models/preprocessor.pkl', 'rb') as f:
        prep = pickle.load(f)
    X_val, _ = engineer_features(val_df.drop(columns=['recovered', 'intervention_timestamp']), fit=False, preprocessor=prep)
    with open('ml/models/recovery_model.pkl', 'rb') as f:
        model = pickle.load(f)
        
    r = permutation_importance(model, X_val, yv, n_repeats=5, random_state=42)
    df = pd.DataFrame({'feature': X_val.columns, 'importance': r.importances_mean}).sort_values('importance', ascending=False)
    print("Top 10 features:")
    for i, row in df.head(10).iterrows():
        print(f"{row['feature']}: {row['importance']:.4f}")

if __name__ == '__main__':
    main()
