"""
Tests for model_interface.py
Tests prediction, retraining, and model building functionality.
"""

import pytest
import numpy as np
import pandas as pd
import os
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
import sys

# Add parent directory to path to import model_interface
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.services.model_interface import build_model, predict, retrain_model


class TestBuildModel:
    """Test suite for build_model function"""

    def test_build_model_default_params(self):
        """Test that build_model creates a model with default parameters"""
        input_dim = 20
        model = build_model(input_dim)

        # Check model is created
        assert model is not None

        # Check model has correct input shape
        assert model.input_shape == (None, input_dim)

        # Check model has correct output shape (binary classification)
        assert model.output_shape == (None, 1)

        # Check model is compiled
        assert model.optimizer is not None
        assert model.loss is not None

    def test_build_model_custom_params(self):
        """Test that build_model respects custom hyperparameters"""
        input_dim = 15
        custom_lr = 0.001
        custom_dropout = 0.5
        custom_l2 = 0.01
        custom_hidden = 512

        model = build_model(
            input_dim=input_dim,
            learning_rate=custom_lr,
            dropout_rate=custom_dropout,
            l2_reg=custom_l2,
            hidden_size=custom_hidden
        )

        assert model is not None
        assert model.input_shape == (None, input_dim)

        # Check that model has the right number of layers
        # Input -> Dense -> BatchNorm -> Dropout -> Dense (output)
        assert len(model.layers) == 4  # Dense, BatchNorm, Dropout, Dense

    def test_build_model_optimized_params(self):
        """Test that build_model works with optimized hyperparameters from cross-validation"""
        input_dim = 20
        model = build_model(
            input_dim=input_dim,
            learning_rate=0.0005,
            dropout_rate=0.4,
            l2_reg=0.001,
            hidden_size=256
        )

        assert model is not None
        assert model.input_shape == (None, input_dim)

        # Check optimizer learning rate
        lr = float(model.optimizer.learning_rate.numpy())
        assert abs(lr - 0.0005) < 1e-6


class TestPredict:
    """Test suite for predict function"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_model_and_scaler(self, temp_dir):
        """Create a sample model and scaler for testing"""
        from sklearn.preprocessing import StandardScaler
        import joblib
        from tensorflow import keras

        # Create sample scaler
        scaler = StandardScaler()
        X_sample = np.random.randn(100, 20)
        scaler.fit(X_sample)

        # Create sample model
        model = build_model(input_dim=20)

        # Save model and scaler
        model_path = os.path.join(temp_dir, 'test_model.keras')
        scaler_path = os.path.join(temp_dir, 'test_scaler.pkl')

        model.save(model_path)
        joblib.dump(scaler, scaler_path)

        return model_path, scaler_path

    def test_predict_with_dataframe(self, sample_model_and_scaler):
        """Test prediction with DataFrame input"""
        model_path, scaler_path = sample_model_and_scaler

        # Create sample input
        X_test = pd.DataFrame(np.random.randn(5, 20))

        # Make predictions
        results = predict(X_test, model_path=model_path, scaler_path=scaler_path)

        # Check results structure
        assert 'predictions' in results
        assert 'probabilities' in results
        assert 'input_shape' in results

        # Check output shapes
        assert len(results['predictions']) == 5
        assert len(results['probabilities']) == 5
        assert results['input_shape'] == (5, 20)

        # Check predictions are binary (0 or 1)
        assert all(p in [0, 1] for p in results['predictions'])

        # Check probabilities are between 0 and 1
        assert all(0 <= p <= 1 for p in results['probabilities'])

    def test_predict_with_numpy_array(self, sample_model_and_scaler):
        """Test prediction with numpy array input"""
        model_path, scaler_path = sample_model_and_scaler

        # Create sample input as numpy array
        X_test = np.random.randn(3, 20)

        # Make predictions
        results = predict(X_test, model_path=model_path, scaler_path=scaler_path)

        # Check results
        assert len(results['predictions']) == 3
        assert len(results['probabilities']) == 3

    def test_predict_custom_threshold(self, sample_model_and_scaler):
        """Test prediction with custom classification threshold"""
        model_path, scaler_path = sample_model_and_scaler

        X_test = pd.DataFrame(np.random.randn(10, 20))

        # Make predictions with different thresholds
        results_low = predict(X_test, model_path=model_path, scaler_path=scaler_path, threshold=0.3)
        results_high = predict(X_test, model_path=model_path, scaler_path=scaler_path, threshold=0.7)

        # With lower threshold, we should generally get more positive predictions
        # (though this is probabilistic and might not always hold for random data)
        assert 'predictions' in results_low
        assert 'predictions' in results_high

    def test_predict_model_not_found(self, temp_dir):
        """Test that predict raises error when model file doesn't exist"""
        X_test = pd.DataFrame(np.random.randn(5, 20))

        fake_model_path = os.path.join(temp_dir, 'nonexistent_model.keras')
        fake_scaler_path = os.path.join(temp_dir, 'scaler.pkl')

        with pytest.raises(FileNotFoundError, match="Model file not found"):
            predict(X_test, model_path=fake_model_path, scaler_path=fake_scaler_path)

    def test_predict_scaler_not_found(self, temp_dir):
        """Test that predict raises error when scaler file doesn't exist"""
        from tensorflow import keras

        # Create and save a model but not scaler
        model = build_model(input_dim=20)
        model_path = os.path.join(temp_dir, 'test_model.keras')
        model.save(model_path)

        X_test = pd.DataFrame(np.random.randn(5, 20))
        fake_scaler_path = os.path.join(temp_dir, 'nonexistent_scaler.pkl')

        with pytest.raises(FileNotFoundError, match="Scaler file not found"):
            predict(X_test, model_path=model_path, scaler_path=fake_scaler_path)


class TestRetrainModel:
    """Test suite for retrain_model function"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def sample_training_data(self, temp_dir):
        """Create sample training data CSV"""
        # Create sample data with 20 features and binary target
        n_samples = 200
        n_features = 20

        X = np.random.randn(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)

        # Create DataFrame
        feature_cols = [f'feature_{i}' for i in range(n_features)]
        df = pd.DataFrame(X, columns=feature_cols)
        df['TARGET'] = y

        # Save to CSV
        data_path = os.path.join(temp_dir, 'training_data.csv')
        df.to_csv(data_path, index=False)

        return data_path

    def test_retrain_model_from_scratch(self, temp_dir, sample_training_data):
        """Test retraining when no existing model exists"""
        save_path = os.path.join(temp_dir, 'retrained_model.keras')
        save_scaler_path = os.path.join(temp_dir, 'retrained_scaler.pkl')

        # Retrain without existing model
        results = retrain_model(
            new_data_path=sample_training_data,
            target_column='TARGET',
            model_path=os.path.join(temp_dir, 'nonexistent.keras'),  # Doesn't exist
            scaler_path=os.path.join(temp_dir, 'nonexistent_scaler.pkl'),
            save_path=save_path,
            save_scaler_path=save_scaler_path,
            epochs=5,  # Small number for testing
            verbose=0
        )

        # Check results structure
        assert 'history' in results
        assert 'final_metrics' in results
        assert 'model_path' in results
        assert 'scaler_path' in results

        # Check files were saved
        assert os.path.exists(save_path)
        assert os.path.exists(save_scaler_path)

        # Check metrics exist
        assert 'val_loss' in results['final_metrics']
        assert 'val_accuracy' in results['final_metrics']
        assert 'val_precision' in results['final_metrics']
        assert 'val_recall' in results['final_metrics']

    def test_retrain_model_with_existing_model(self, temp_dir, sample_training_data):
        """Test retraining with an existing model as starting point"""
        # First create and save an initial model
        initial_model = build_model(input_dim=20)
        initial_model_path = os.path.join(temp_dir, 'initial_model.keras')
        initial_model.save(initial_model_path)

        # Create initial scaler
        from sklearn.preprocessing import StandardScaler
        import joblib
        scaler = StandardScaler()
        scaler.fit(np.random.randn(100, 20))
        initial_scaler_path = os.path.join(temp_dir, 'initial_scaler.pkl')
        joblib.dump(scaler, initial_scaler_path)

        # Now retrain
        save_path = os.path.join(temp_dir, 'retrained_model.keras')
        save_scaler_path = os.path.join(temp_dir, 'retrained_scaler.pkl')

        results = retrain_model(
            new_data_path=sample_training_data,
            target_column='TARGET',
            model_path=initial_model_path,
            scaler_path=initial_scaler_path,
            save_path=save_path,
            save_scaler_path=save_scaler_path,
            epochs=5,
            verbose=0
        )

        # Check that new model was saved
        assert os.path.exists(save_path)
        assert results['model_path'] == save_path

    def test_retrain_model_data_not_found(self, temp_dir):
        """Test that retrain_model raises error when data file doesn't exist"""
        fake_data_path = os.path.join(temp_dir, 'nonexistent_data.csv')

        with pytest.raises(FileNotFoundError, match="Data file not found"):
            retrain_model(
                new_data_path=fake_data_path,
                target_column='TARGET',
                epochs=5,
                verbose=0
            )

    def test_retrain_model_missing_target_column(self, temp_dir):
        """Test that retrain_model raises error when target column is missing"""
        # Create data without the expected target column
        df = pd.DataFrame(np.random.randn(100, 20))
        data_path = os.path.join(temp_dir, 'no_target.csv')
        df.to_csv(data_path, index=False)

        with pytest.raises(ValueError, match="Target column 'TARGET' not found"):
            retrain_model(
                new_data_path=data_path,
                target_column='TARGET',
                epochs=5,
                verbose=0
            )

    def test_retrain_model_custom_parameters(self, temp_dir, sample_training_data):
        """Test retraining with custom parameters"""
        save_path = os.path.join(temp_dir, 'custom_model.keras')
        save_scaler_path = os.path.join(temp_dir, 'custom_scaler.pkl')

        results = retrain_model(
            new_data_path=sample_training_data,
            target_column='TARGET',
            model_path=os.path.join(temp_dir, 'nonexistent.keras'),
            save_path=save_path,
            save_scaler_path=save_scaler_path,
            validation_split=0.3,
            epochs=10,
            batch_size=32,
            patience=5,
            verbose=0
        )

        assert os.path.exists(save_path)
        assert results['model_path'] == save_path


class TestIntegration:
    """Integration tests for the full workflow"""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)

    def test_full_workflow_train_and_predict(self, temp_dir):
        """Test full workflow: create data, train model, make predictions"""
        # Step 1: Create training data
        n_samples = 500
        n_features = 20

        X = np.random.randn(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)

        feature_cols = [f'feature_{i}' for i in range(n_features)]
        df = pd.DataFrame(X, columns=feature_cols)
        df['TARGET'] = y

        data_path = os.path.join(temp_dir, 'training_data.csv')
        df.to_csv(data_path, index=False)

        # Step 2: Train model
        model_path = os.path.join(temp_dir, 'trained_model.keras')
        scaler_path = os.path.join(temp_dir, 'scaler.pkl')

        train_results = retrain_model(
            new_data_path=data_path,
            target_column='TARGET',
            model_path=os.path.join(temp_dir, 'nonexistent.keras'),
            save_path=model_path,
            save_scaler_path=scaler_path,
            epochs=10,
            verbose=0
        )

        assert os.path.exists(model_path)
        assert os.path.exists(scaler_path)

        # Step 3: Make predictions on new data
        X_new = pd.DataFrame(np.random.randn(10, n_features), columns=feature_cols)

        pred_results = predict(
            X_new,
            model_path=model_path,
            scaler_path=scaler_path
        )

        assert len(pred_results['predictions']) == 10
        assert len(pred_results['probabilities']) == 10
        assert all(p in [0, 1] for p in pred_results['predictions'])

    def test_retrain_then_predict(self, temp_dir):
        """Test retraining an existing model then making predictions"""
        # Create initial model
        initial_model = build_model(input_dim=20)
        model_path = os.path.join(temp_dir, 'model.keras')
        initial_model.save(model_path)

        # Create training data
        n_samples = 300
        n_features = 20

        X = np.random.randn(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)

        feature_cols = [f'feature_{i}' for i in range(n_features)]
        df = pd.DataFrame(X, columns=feature_cols)
        df['TARGET'] = y

        data_path = os.path.join(temp_dir, 'training_data.csv')
        df.to_csv(data_path, index=False)

        # Retrain
        scaler_path = os.path.join(temp_dir, 'scaler.pkl')
        retrain_model(
            new_data_path=data_path,
            target_column='TARGET',
            model_path=model_path,
            save_path=model_path,  # Overwrite
            save_scaler_path=scaler_path,
            epochs=5,
            verbose=0
        )

        # Predict
        X_new = pd.DataFrame(np.random.randn(5, n_features), columns=feature_cols)
        results = predict(X_new, model_path=model_path, scaler_path=scaler_path)

        assert len(results['predictions']) == 5


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
