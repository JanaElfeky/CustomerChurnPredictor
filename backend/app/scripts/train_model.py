"""
Training script for the churn prediction model.
This script trains/retrains the model and saves it to ml_models/
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.app.services.model_interface import retrain_model, MODEL_PATH, SCALER_PATH


def train_initial_model(data_path, target_column='TARGET'):
    """
    Train the initial model from scratch.

    Args:
        data_path (str): Path to the training data CSV
        target_column (str): Name of the target column

    Returns:
        dict: Training results
    """
    print("=" * 70)
    print("TRAINING INITIAL MODEL")
    print("=" * 70)
    print(f"Data source: {data_path}")
    print(f"Target column: {target_column}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        results = retrain_model(
            new_data_path=data_path,
            target_column=target_column,
            load_existing=False,  # Don't load existing model
            validation_split=0.2,
            epochs=100,
            batch_size=64,
            patience=15,
            verbose=1
        )

        print("\n" + "=" * 70)
        print("TRAINING COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"Model saved to: {results['model_path']}")
        print(f"Scaler saved to: {results['scaler_path']}")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return results

    except Exception as e:
        print("\n" + "=" * 70)
        print("TRAINING FAILED")
        print("=" * 70)
        print(f"Error: {str(e)}")
        raise


def retrain_existing_model(data_path, target_column='TARGET'):
    """
    Retrain the existing model with new data.

    Args:
        data_path (str): Path to the new training data CSV
        target_column (str): Name of the target column

    Returns:
        dict: Training results
    """
    print("=" * 70)
    print("RETRAINING EXISTING MODEL")
    print("=" * 70)
    print(f"Data source: {data_path}")
    print(f"Target column: {target_column}")
    print(f"Current model: {MODEL_PATH}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    try:
        results = retrain_model(
            new_data_path=data_path,
            target_column=target_column,
            load_existing=True,  # Load and continue from existing model
            validation_split=0.2,
            epochs=100,
            batch_size=64,
            patience=15,
            verbose=1
        )

        print("\n" + "=" * 70)
        print("RETRAINING COMPLETED SUCCESSFULLY")
        print("=" * 70)
        print(f"Model updated at: {results['model_path']}")
        print(f"Scaler updated at: {results['scaler_path']}")
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return results

    except Exception as e:
        print("\n" + "=" * 70)
        print("RETRAINING FAILED")
        print("=" * 70)
        print(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Train or retrain the churn prediction model')
    parser.add_argument('data_path', type=str, help='Path to the training data CSV file')
    parser.add_argument('--target', type=str, default='TARGET', help='Name of the target column (default: TARGET)')
    parser.add_argument('--retrain', action='store_true', help='Retrain existing model instead of training from scratch')

    args = parser.parse_args()

    # Check if data file exists
    if not os.path.exists(args.data_path):
        print(f"Error: Data file not found at {args.data_path}")
        sys.exit(1)

    # Train or retrain
    if args.retrain:
        if not os.path.exists(MODEL_PATH):
            print(f"Warning: No existing model found at {MODEL_PATH}")
            print("Training new model from scratch instead...")
            train_initial_model(args.data_path, args.target)
        else:
            retrain_existing_model(args.data_path, args.target)
    else:
        if os.path.exists(MODEL_PATH):
            print(f"Warning: Model already exists at {MODEL_PATH}")
            response = input("Do you want to overwrite it? (yes/no): ")
            if response.lower() != 'yes':
                print("Training cancelled.")
                sys.exit(0)
        train_initial_model(args.data_path, args.target)
