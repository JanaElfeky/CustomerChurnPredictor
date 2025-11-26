import numpy as np
import pandas as pd
import joblib
import os
from sklearn.preprocessing import StandardScaler, MinMaxScaler


def validate_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and convert data types to ensure consistency.
    Handles data from database where types might be stored differently.

    Args:
        df: DataFrame with customer features

    Returns:
        pd.DataFrame: DataFrame with corrected types
    """
    validated_df = df.copy()

    # Define expected types for each feature (using database column names - lowercase)
    BOOLEAN_FEATURES = ['pack_102', 'pack_103', 'pack_104', 'pack_105']
    INTEGER_FEATURES = ['id', 'age', 'clnt_setup_tenor']
    # All other numeric features should be float

    # Convert boolean features
    for feature in BOOLEAN_FEATURES:
        if feature in validated_df.columns:
            # Handle various boolean representations: 0/1, "True"/"False", True/False
            validated_df[feature] = validated_df[feature].astype(bool)

    # Convert integer features
    for feature in INTEGER_FEATURES:
        if feature in validated_df.columns:
            validated_df[feature] = validated_df[feature].astype(int)

    # Convert all other numeric columns to float (except id, target, and boolean columns)
    for column in validated_df.columns:
        if column.lower() not in BOOLEAN_FEATURES + INTEGER_FEATURES + ['target']:
            if pd.api.types.is_numeric_dtype(validated_df[column]):
                validated_df[column] = validated_df[column].astype(float)

    return validated_df


def preprocess_and_fit(input_df: pd.DataFrame, scaler_path: str = None) -> tuple:
    """
    Preprocess training data and fit scalers.
    Use this during model training to create and save scalers.

    Args:
        input_df: DataFrame with features (and optionally TARGET)
        scaler_path: Path to save the scalers dict (optional)

    Returns:
        tuple: (processed_df, scalers_dict)
    """
    # Validate and convert types first
    validated_df = validate_types(input_df)

    # Make a copy to avoid modifying in-place
    processed_df = validated_df.copy()
    scalers = {}

    for feature in processed_df.columns:
        # Skip ID and TARGET columns (case-insensitive)
        if feature.upper() in ['ID', 'TARGET']:
            continue

        # Assess distribution (skewness)
        data = processed_df[feature]
        skewness = data.skew() if isinstance(data, pd.Series) else 0

        # Select scaler based on distribution
        if abs(skewness) < 0.5:
            scaler = StandardScaler()
        else:
            scaler = MinMaxScaler()

        # Fit and transform feature
        processed_df[feature] = scaler.fit_transform(processed_df[[feature]])
        scalers[feature] = scaler

    # Save scalers if path provided
    if scaler_path:
        os.makedirs(os.path.dirname(scaler_path), exist_ok=True)
        joblib.dump(scalers, scaler_path)
        print(f"Scalers saved to {scaler_path}")

    return processed_df, scalers


def preprocess_with_scalers(input_df: pd.DataFrame, scaler_path: str) -> pd.DataFrame:
    """
    Preprocess data using pre-fitted scalers.
    Use this during prediction with saved scalers from training.

    Args:
        input_df: DataFrame with features
        scaler_path: Path to the saved scalers dict

    Returns:
        pd.DataFrame: Preprocessed data
    """
    if not os.path.exists(scaler_path):
        raise FileNotFoundError(f"Scaler file not found at {scaler_path}")

    # Validate and convert types first
    validated_df = validate_types(input_df)

    # Load saved scalers
    scalers = joblib.load(scaler_path)

    # Make a copy
    processed_df = validated_df.copy()

    for feature in processed_df.columns:
        # Skip ID and TARGET columns (case-insensitive)
        if feature.upper() in ['ID', 'TARGET']:
            continue

        if feature not in scalers:
            raise ValueError(f"No scaler found for feature: {feature}")

        # Transform using saved scaler
        scaler = scalers[feature]
        processed_df[feature] = scaler.transform(processed_df[[feature]])

    return processed_df


def preprocess_record(input_df: pd.DataFrame) -> pd.DataFrame:
    """
    Legacy function - kept for backward compatibility.
    For new code, use preprocess_and_fit() for training or
    preprocess_with_scalers() for prediction.
    """
    # Validate and convert types first
    validated_df = validate_types(input_df)

    processed_df = validated_df.copy()
    scalers = {}

    for feature in processed_df.columns:
        # Skip ID and TARGET columns (case-insensitive)
        if feature.upper() in ['ID', 'TARGET']:
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
