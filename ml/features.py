import pandas as pd
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer

def get_feature_pipeline():
    """
    Returns a scikit-learn ColumnTransformer for reproducible feature engineering.
    Handles missing values, scaling, and categorical encoding.
    Ensures strict separation and avoids data leakage by only using predefined features.
    """
    
    # 1. Define feature groups
    # Note: 'recovered' and 'intervention_timestamp' are STRICTLY excluded to prevent leakage.
    
    numeric_features = [
        'amount', 
        'transaction_hour',
        'transaction_day',
        'amount_relative_to_customer_average',
        'previous_failure_count',
        'total_previous_payments',
        'successful_payments',
        'failed_payments',
        'historical_success_rate',
        'customer_tenure',
        'average_transaction_amount',
        'previous_intervention_count',
        'previous_successful_recoveries',
        'historical_recovery_rate',
        'time_since_last_intervention',
        'previous_subscription_failures'
    ]
    
    categorical_features = [
        'currency',
        'payment_method',
        'error_code',
        'root_cause_diagnosis',
        'subscription_status'
    ]
    
    # 2. Numeric pipeline: Impute missing with median, then scale
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', StandardScaler())
    ])
    
    # 3. Categorical pipeline: Impute missing with 'missing', then one-hot encode
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    # 4. Combine into a ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ],
        remainder='drop'  # Explicitly drop any columns not specified above to prevent leakage
    )
    
    return preprocessor, numeric_features, categorical_features

def engineer_features(df: pd.DataFrame, fit=True, preprocessor=None):
    """
    Applies the feature pipeline to the dataframe.
    """
    if fit or preprocessor is None:
        preprocessor, num_cols, cat_cols = get_feature_pipeline()
        X_transformed = preprocessor.fit_transform(df)
    else:
        X_transformed = preprocessor.transform(df)
        
    # Reconstruct dataframe with feature names for interpretability
    # Get feature names out from the ColumnTransformer
    try:
        feature_names = preprocessor.get_feature_names_out()
    except AttributeError:
        # Fallback if get_feature_names_out fails
        feature_names = [f"f_{i}" for i in range(X_transformed.shape[1])]
        
    df_features = pd.DataFrame(X_transformed, columns=feature_names, index=df.index)
    return df_features, preprocessor

if __name__ == "__main__":
    # Quick test
    import os
    if os.path.exists("synthetic_recovery_data.csv"):
        df = pd.read_csv("synthetic_recovery_data.csv")
        X, prep = engineer_features(df)
        print(f"Feature engineering successful. Shape: {X.shape}")
        print("Features generated:")
        print(X.columns[:10].tolist() + ["..."])
