import numpy as np
import pandas as pd
import os

# Configure TensorFlow before importing it
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Suppress TensorFlow warnings
os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # Force CPU usage, disable GPU

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, callbacks
from tensorflow.keras.losses import BinaryFocalCrossentropy
from sklearn.utils.class_weight import compute_class_weight
from app.services.preprocesser import preprocess_and_fit, preprocess_with_scalers

# Reproducibility
np.random.seed(42)
tf.random.set_seed(42)

# Model paths
ML_MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml_models')
MODEL_PATH = os.path.join(ML_MODELS_DIR, 'model.keras')
SCALER_PATH = os.path.join(ML_MODELS_DIR, 'scaler.pkl')


# Build neural network with optimized hyperparameters from Phase 3
def build_model(input_dim, learning_rate=0.0005, dropout_rate=0.4, l2_reg=0.001, hidden_size=256):
    model = keras.Sequential([
        layers.Input(shape=(input_dim,)),
        layers.Dense(hidden_size, activation='relu', kernel_regularizer=keras.regularizers.l2(l2_reg)),
        layers.BatchNormalization(),
        layers.Dropout(dropout_rate),
        layers.Dense(1, activation='sigmoid')
    ])

    # Focal loss handles class imbalance
    loss_fn = BinaryFocalCrossentropy(gamma=2, from_logits=False, alpha=0.25)

    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=learning_rate),
        loss=loss_fn,
        metrics=['accuracy', keras.metrics.Precision(name='precision'),
                 keras.metrics.Recall(name='recall'), keras.metrics.AUC(name='auc')]
    )

    return model


# Predict churn for new data using trained model
def predict(input_data, model_path=None, scaler_path=None, threshold=0.5):
    if model_path is None:
        model_path = MODEL_PATH
    if scaler_path is None:
        scaler_path = SCALER_PATH

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model not found: {model_path}")

    model = keras.models.load_model(model_path)

    # Convert to DataFrame
    if isinstance(input_data, np.ndarray):
        input_data = pd.DataFrame(input_data)

    # Preprocess using saved scalers
    input_scaled = preprocess_with_scalers(input_data, scaler_path)

    # Drop ID column if present
    id_cols = [col for col in input_scaled.columns if col.upper() == 'ID']
    if id_cols:
        input_scaled = input_scaled.drop(columns=id_cols)

    # Predict
    probabilities = model.predict(input_scaled).flatten()
    predictions = (probabilities >= threshold).astype(int)

    return {
        'predictions': predictions,
        'probabilities': probabilities,
        'input_shape': input_data.shape
    }


# Retrain model on new labeled data
def retrain_model(new_data_path, target_column='TARGET', load_existing=True,
                  validation_split=0.0, epochs=100, batch_size=64, patience=15, verbose=1):
    if not os.path.exists(new_data_path):
        raise FileNotFoundError(f"Data not found: {new_data_path}")

    df = pd.read_csv(new_data_path)

    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' not found")

    # Drop ID and target columns
    columns_to_drop = [target_column]
    id_cols = [col for col in df.columns if col.lower() == 'id']
    if id_cols:
        columns_to_drop.extend(id_cols)
        print(f"Dropping ID: {id_cols}")

    X = df.drop(columns_to_drop, axis=1)
    y = df[target_column]

    # Preprocess and save scalers
    print("Preprocessing data")
    X_scaled, _ = preprocess_and_fit(X, scaler_path=SCALER_PATH)

    # Load existing model or build new one
    if load_existing and os.path.exists(MODEL_PATH):
        print(f"Loading existing model from {MODEL_PATH}")
        model = keras.models.load_model(MODEL_PATH)
    else:
        print("Building new model")
        model = build_model(
            input_dim=X_scaled.shape[1],
            learning_rate=0.0005,
            dropout_rate=0.4,
            l2_reg=0.001,
            hidden_size=256
        )

    # Calculate class weights for imbalanced data
    classes = np.unique(y)
    class_weights = compute_class_weight(class_weight='balanced', classes=classes, y=y)
    class_weight_dict = dict(zip(classes, class_weights))
    print(f"Class weights: {class_weight_dict}")

    # Recompile with focal loss
    loss_fn = BinaryFocalCrossentropy(gamma=2, from_logits=False, alpha=0.25)
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.0005),
        loss=loss_fn,
        metrics=['accuracy', keras.metrics.Precision(name='precision'),
                 keras.metrics.Recall(name='recall'), keras.metrics.AUC(name='auc')]
    )

    # Train on entire labeled dataset (no validation split for retraining)
    print(f"\nRetraining on {len(X_scaled)} samples (using all labeled data)")
    history = model.fit(
        X_scaled, y,
        epochs=epochs,
        batch_size=batch_size,
        validation_split=validation_split,
        verbose=verbose,
        class_weight=class_weight_dict
    )

    # Save model
    os.makedirs(ML_MODELS_DIR, exist_ok=True)
    model.save(MODEL_PATH)
    print(f"\nModel saved to {MODEL_PATH}")

    # Final metrics (training metrics only since no validation split)
    final_metrics = {
        'loss': history.history['loss'][-1],
        'accuracy': history.history['accuracy'][-1],
        'precision': history.history['precision'][-1],
        'recall': history.history['recall'][-1],
        'auc': history.history['auc'][-1]
    }

    print("\nFinal training metrics:")
    for metric, value in final_metrics.items():
        print(f"  {metric}: {value:.4f}")

    return {
        'history': history,
        'final_metrics': final_metrics,
        'model_path': MODEL_PATH,
        'scaler_path': SCALER_PATH
    }
