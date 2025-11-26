"""
Model Interface for Customer Churn Prediction
Provides functions for prediction and retraining using the optimized neural network model.
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, callbacks
from tensorflow.keras.losses import BinaryFocalCrossentropy
from sklearn.utils.class_weight import compute_class_weight
import os
from app.services.preprocesser import preprocess_and_fit, preprocess_with_scalers


# Set random seeds for reproducibility
np.random.seed(42)
tf.random.set_seed(42)

# Base directory for ML models
ML_MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml_models')
MODEL_PATH = os.path.join(ML_MODELS_DIR, 'model.keras')
SCALER_PATH = os.path.join(ML_MODELS_DIR, 'scaler.pkl')


def build_model(input_dim, learning_rate=0.0005, dropout_rate=0.4, l2_reg=0.001, hidden_size=256):
    """
    Build neural network model with optimized hyperparameters from cross-validation.

    Args:
        input_dim (int): Number of input features
        learning_rate (float): Learning rate for Adam optimizer (default: 0.0005)
        dropout_rate (float): Dropout rate for regularization (default: 0.4)
        l2_reg (float): L2 regularization parameter (default: 0.001)
        hidden_size (int): Number of neurons in hidden layer (default: 256)

    Returns:
        keras.Model: Compiled neural network model
    """
    model = keras.Sequential([
        layers.Input(shape=(input_dim,)),

        # Hidden layer
        layers.Dense(hidden_size, activation='relu',
                     kernel_regularizer=keras.regularizers.l2(l2_reg)),
        layers.BatchNormalization(),
        layers.Dropout(dropout_rate),

        # Output layer
        layers.Dense(1, activation='sigmoid')
    ])

    # Use BinaryFocalCrossentropy loss for better handling of class imbalance
    loss_fn = BinaryFocalCrossentropy(gamma=2, from_logits=False, alpha=0.25)

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss=loss_fn,
        metrics=[
            'accuracy',
            keras.metrics.Precision(name='precision'),
            keras.metrics.Recall(name='recall'),
            keras.metrics.AUC(name='auc')
        ]
    )

    return model


def predict(input_data, model_path=None, scaler_path=None, threshold=0.5):
    """
    Predict churn probability for new input data using a trained model.
    If model_path and scaler_path are not provided, uses the default model.

    Args:
        input_data (pd.DataFrame or np.ndarray): Input features for prediction
        model_path (str, optional): Path to the saved model file. If None, uses default model.
        scaler_path (str, optional): Path to the saved scaler file. If None, uses default scaler.
        threshold (float): Classification threshold (default: 0.5)

    Returns:
        dict: Dictionary containing predictions and probabilities
            - 'predictions': Binary predictions (0 or 1)
            - 'probabilities': Churn probabilities
            - 'input_shape': Shape of input data
    """
    # If paths not provided, use default model paths
    if model_path is None:
        model_path = MODEL_PATH
    if scaler_path is None:
        scaler_path = SCALER_PATH

    # Load the trained model
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at {model_path}")

    model = keras.models.load_model(model_path)

    # Convert input to DataFrame if it's a numpy array
    if isinstance(input_data, np.ndarray):
        input_data = pd.DataFrame(input_data)

    # Preprocess the input data using saved scalers from preprocessor
    input_scaled = preprocess_with_scalers(input_data, scaler_path)

    # Drop ID column if present (case-insensitive)
    id_cols = [col for col in input_scaled.columns if col.upper() == 'ID']
    if id_cols:
        input_scaled = input_scaled.drop(columns=id_cols)

    # Make predictions
    probabilities = model.predict(input_scaled).flatten()
    predictions = (probabilities >= threshold).astype(int)

    return {
        'predictions': predictions,
        'probabilities': probabilities,
        'input_shape': input_data.shape
    }


def retrain_model(new_data_path, target_column='TARGET',
                  load_existing=True,
                  validation_split=0.2,
                  epochs=100,
                  batch_size=64,
                  patience=15,
                  verbose=1):
    """
    Retrain the model on new labeled data using optimized hyperparameters.
    The retrained model will overwrite the existing model at ml_models/model.keras

    Args:
        new_data_path (str): Path to CSV file with new labeled data
        target_column (str): Name of the target column (default: 'TARGET')
        load_existing (bool): Whether to load existing model as starting point (default: True)
        validation_split (float): Fraction of data to use for validation (default: 0.2)
        epochs (int): Maximum number of training epochs (default: 100)
        batch_size (int): Batch size for training (default: 64)
        patience (int): Early stopping patience (default: 15)
        verbose (int): Verbosity mode (0, 1, or 2)

    Returns:
        dict: Dictionary containing training history and metrics
            - 'history': Training history object
            - 'final_metrics': Final validation metrics
            - 'model_path': Path where model was saved
            - 'scaler_path': Path where scaler was saved
    """
    # Load new data
    if not os.path.exists(new_data_path):
        raise FileNotFoundError(f"Data file not found at {new_data_path}")

    df = pd.read_csv(new_data_path)

    # Separate features and target
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found in data")

    X = df.drop(target_column, axis=1)
    y = df[target_column]

    # Preprocess data using the preprocessor (per-feature scaling based on skewness)
    print("Preprocessing data...")
    X_scaled, _ = preprocess_and_fit(X, scaler_path=SCALER_PATH)

    # Load existing model as starting point or build new one
    if load_existing and os.path.exists(MODEL_PATH):
        print(f"Loading existing model from {MODEL_PATH}...")
        model = keras.models.load_model(MODEL_PATH)
    else:
        print("Building new model...")
        model = build_model(
            input_dim=X_scaled.shape[1],
            learning_rate=0.0005,
            dropout_rate=0.4,
            l2_reg=0.001,
            hidden_size=256
        )

    # Calculate class weights for handling imbalanced data
    classes = np.unique(y)
    class_weights = compute_class_weight(class_weight='balanced', classes=classes, y=y)
    class_weight_dict = dict(zip(classes, class_weights))

    print(f"Class weights: {class_weight_dict}")

    # Setup early stopping callback
    early_stop = callbacks.EarlyStopping(
        monitor='val_loss',
        patience=patience,
        restore_best_weights=True,
        verbose=verbose
    )

    # Recompile model with optimized hyperparameters
    loss_fn = BinaryFocalCrossentropy(gamma=2, from_logits=False, alpha=0.25)
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.0005),
        loss=loss_fn,
        metrics=[
            'accuracy',
            keras.metrics.Precision(name='precision'),
            keras.metrics.Recall(name='recall'),
            keras.metrics.AUC(name='auc')
        ]
    )

    # Train the model
    print(f"\nRetraining model on {len(X_scaled)} samples...")
    history = model.fit(
        X_scaled, y,
        epochs=epochs,
        batch_size=batch_size,
        validation_split=validation_split,
        callbacks=[early_stop],
        verbose=verbose,
        class_weight=class_weight_dict
    )

    # Create models directory if it doesn't exist
    os.makedirs(ML_MODELS_DIR, exist_ok=True)

    # Save retrained model (overwrites existing model)
    model.save(MODEL_PATH)
    print(f"\nRetrained model saved to {MODEL_PATH}")
    # Note: Scalers already saved by preprocess_and_fit

    # Get final validation metrics
    final_metrics = {
        'val_loss': history.history['val_loss'][-1],
        'val_accuracy': history.history['val_accuracy'][-1],
        'val_precision': history.history['val_precision'][-1],
        'val_recall': history.history['val_recall'][-1],
        'val_auc': history.history['val_auc'][-1]
    }

    print("\nFinal Validation Metrics:")
    for metric, value in final_metrics.items():
        print(f"  {metric}: {value:.4f}")

    return {
        'history': history,
        'final_metrics': final_metrics,
        'model_path': MODEL_PATH,
        'scaler_path': SCALER_PATH
    }


if __name__ == "__main__":
    # Example usage
    print("Model Interface Module")
    print("=" * 50)
    print("\nFunctions available:")
    print("  - predict(): Predict churn for new input data")
    print("  - retrain_model(): Retrain model on new labeled data")
    print("  - build_model(): Build model with optimized hyperparameters")
