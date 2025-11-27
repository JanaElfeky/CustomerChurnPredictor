"""
Model versioning system to maintain multiple versions of trained models.
Keeps the 3 most recent model versions with metadata.
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ModelVersionManager:
    """
    Manages versioning of ML models, keeping the 3 most recent versions.
    """

    def __init__(self, models_dir, max_versions=3):
        """
        Initialize the model version manager.

        Args:
            models_dir (str): Directory where models are stored
            max_versions (int): Maximum number of versions to keep (default: 3)
        """
        self.models_dir = Path(models_dir)
        self.versions_dir = self.models_dir / "versions"
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.max_versions = max_versions
        self.metadata_file = self.versions_dir / "versions_metadata.json"

    def _load_metadata(self):
        """Load version metadata from file."""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {"versions": []}

    def _save_metadata(self, metadata):
        """Save version metadata to file."""
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def save_new_version(self, model_path, scaler_path, metrics, training_info):
        """
        Save a new model version with metadata.

        Args:
            model_path (str): Path to the model file
            scaler_path (str): Path to the scaler file
            metrics (dict): Training metrics (accuracy, loss, etc.)
            training_info (dict): Additional training information (samples, epochs, etc.)

        Returns:
            dict: Information about the saved version
        """
        try:
            # Generate version ID and timestamp (use UTC to match database timestamps)
            timestamp = datetime.utcnow()
            version_id = timestamp.strftime("%Y%m%d_%H%M%S")
            version_dir = self.versions_dir / f"v_{version_id}"
            version_dir.mkdir(exist_ok=True)

            # Copy model and scaler to version directory
            model_name = Path(model_path).name
            scaler_name = Path(scaler_path).name

            versioned_model_path = version_dir / model_name
            versioned_scaler_path = version_dir / scaler_name

            shutil.copy2(model_path, versioned_model_path)
            shutil.copy2(scaler_path, versioned_scaler_path)

            # Create version metadata
            version_metadata = {
                "version_id": version_id,
                "timestamp": timestamp.isoformat(),
                "model_path": str(versioned_model_path),
                "scaler_path": str(versioned_scaler_path),
                "metrics": metrics,
                "training_info": training_info
            }

            # Load existing metadata
            metadata = self._load_metadata()

            # Add new version
            metadata["versions"].append(version_metadata)

            # Sort by timestamp (newest first)
            metadata["versions"].sort(key=lambda v: v["timestamp"], reverse=True)

            # Keep only the most recent versions
            if len(metadata["versions"]) > self.max_versions:
                # Delete old version directories
                for old_version in metadata["versions"][self.max_versions:]:
                    old_dir = Path(old_version["model_path"]).parent
                    if old_dir.exists():
                        shutil.rmtree(old_dir)
                        logger.info(f"Deleted old version: {old_version['version_id']}")

                # Keep only max_versions in metadata
                metadata["versions"] = metadata["versions"][:self.max_versions]

            # Mark latest version
            if metadata["versions"]:
                metadata["latest_version"] = metadata["versions"][0]["version_id"]

            # Save updated metadata
            self._save_metadata(metadata)

            logger.info(f"Saved model version {version_id}")
            logger.info(f"Total versions: {len(metadata['versions'])}")

            return version_metadata

        except Exception as e:
            logger.error(f"Error saving model version: {str(e)}", exc_info=True)
            raise

    def get_latest_version(self):
        """
        Get information about the latest model version.

        Returns:
            dict: Latest version metadata, or None if no versions exist
        """
        metadata = self._load_metadata()
        if metadata["versions"]:
            return metadata["versions"][0]
        return None

    def get_version(self, version_id):
        """
        Get information about a specific version.

        Args:
            version_id (str): Version ID to retrieve

        Returns:
            dict: Version metadata, or None if not found
        """
        metadata = self._load_metadata()
        for version in metadata["versions"]:
            if version["version_id"] == version_id:
                return version
        return None

    def list_versions(self):
        """
        List all available model versions.

        Returns:
            list: List of version metadata dictionaries
        """
        metadata = self._load_metadata()
        return metadata["versions"]

    def restore_version(self, version_id, target_model_path, target_scaler_path):
        """
        Restore a specific version as the current model.

        Args:
            version_id (str): Version ID to restore
            target_model_path (str): Where to copy the model
            target_scaler_path (str): Where to copy the scaler

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            version = self.get_version(version_id)
            if not version:
                logger.error(f"Version {version_id} not found")
                return False

            # Copy versioned files to target locations
            shutil.copy2(version["model_path"], target_model_path)
            shutil.copy2(version["scaler_path"], target_scaler_path)

            logger.info(f"Restored version {version_id} to current model")
            return True

        except Exception as e:
            logger.error(f"Error restoring version {version_id}: {str(e)}", exc_info=True)
            return False

    def get_version_summary(self):
        """
        Get a summary of all versions with key metrics.

        Returns:
            list: List of version summaries
        """
        versions = self.list_versions()
        summaries = []

        for v in versions:
            summary = {
                "version_id": v["version_id"],
                "timestamp": v["timestamp"],
                "accuracy": v["metrics"].get("val_accuracy") or v["metrics"].get("accuracy"),
                "auc": v["metrics"].get("val_auc") or v["metrics"].get("auc"),
                "recall": v["metrics"].get("val_recall") or v["metrics"].get("recall"),
                "precision": v["metrics"].get("val_precision") or v["metrics"].get("precision"),
                "samples": v["training_info"].get("total_samples")
            }
            summaries.append(summary)

        return summaries
