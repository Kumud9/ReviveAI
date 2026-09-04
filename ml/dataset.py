import pandas as pd
import numpy as np

def create_time_based_split(df: pd.DataFrame, time_col='intervention_timestamp', train_frac=0.7, val_frac=0.15, test_frac=0.15):
    """
    Creates a reproducible, time-aware split of the dataset.
    Prevents temporal leakage by ensuring:
    - Train data is older than Validation data
    - Validation data is older than Test data
    """
    
    assert abs(train_frac + val_frac + test_frac - 1.0) < 1e-5, "Fractions must sum to 1.0"
    
    # Ensure dataframe is sorted by time
    df_sorted = df.sort_values(by=time_col).reset_index(drop=True)
    
    n_total = len(df_sorted)
    n_train = int(n_total * train_frac)
    n_val = int(n_total * val_frac)
    
    train_df = df_sorted.iloc[:n_train].copy()
    val_df = df_sorted.iloc[n_train:n_train+n_val].copy()
    test_df = df_sorted.iloc[n_train+n_val:].copy()
    
    # Define observation window constraints (Leakage prevention documentation)
    # The `recovered` label is assumed to be resolved at the time of feature extraction.
    # In a real streaming system, we must ensure we only use features available AT the intervention_timestamp.
    
    return train_df, val_df, test_df

def prepare_ml_data(csv_path: str):
    """
    Utility to load, split, and extract targets.
    """
    df = pd.read_csv(csv_path)
    # Convert string timestamp back to datetime if necessary
    df['intervention_timestamp'] = pd.to_datetime(df['intervention_timestamp'])
    
    train_df, val_df, test_df = create_time_based_split(df)
    
    y_train = train_df['recovered']
    y_val = val_df['recovered']
    y_test = test_df['recovered']
    
    return train_df, val_df, test_df, y_train, y_val, y_test

if __name__ == "__main__":
    import os
    if os.path.exists("synthetic_recovery_data.csv"):
        train, val, test, yt, yv, yte = prepare_ml_data("synthetic_recovery_data.csv")
        print(f"Time-aware split complete.")
        print(f"Train: {len(train)} rows")
        print(f"Val: {len(val)} rows")
        print(f"Test: {len(test)} rows")
