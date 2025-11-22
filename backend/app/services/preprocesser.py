import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, MinMaxScaler


def preprocess_record(input_df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess input data for model inference.
    Assumes input_df follows schema (validated), with features as columns.
    Applies per-feature normalization using either StandardScaler or MinMaxScaler
    based on feature distribution.
    """
    # Make a copy to avoid modifying in-place
    processed_df = input_df.copy()
    scalers = {}
    for feature in processed_df.columns:
        if feature in ['ID', 'TARGET']:
            continue
        # Assess distribution (skewness)
        data = processed_df[feature]
        skewness = data.skew() if isinstance(data, pd.Series) else 0

        # Select scaler
        if abs(skewness) < 0.5:
            scaler = StandardScaler()
        else:
            scaler = MinMaxScaler()

        # Fit and transform feature
        processed_df[feature] = scaler.fit_transform(processed_df[[feature]])
        scalers[feature] = scaler
    return processed_df
