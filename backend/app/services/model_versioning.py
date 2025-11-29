import os
import json
import shutil
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ModelVersionManager:
    # mananges model versions
    def __init__(self, models_dir, max_versions=3):
        self.models_dir = Path(models_dir)
        self.versions_dir = self.models_dir / "versions"
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        self.max_versions = max_versions
        self.metadata_file = self.versions_dir / "versions_metadata.json"

    # Load existing metadata
    def _load_metadata(self):
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return {"versions": []}

    # Save metadata to file
    def _save_metadata(self, metadata):
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    # Save a new model version
    def save_new_version(self, model_path, scaler_path, metrics, training_info):
        try:
            timestamp = datetime.utcnow()
            version_id = timestamp.strftime("%Y%m%d_%H%M%S")
            version_dir = self.versions_dir / f"v_{version_id}"
            version_dir.mkdir(exist_ok=True)

            versioned_model_path = version_dir / Path(model_path).name
            versioned_scaler_path = version_dir / Path(scaler_path).name

            shutil.copy2(model_path, versioned_model_path)
            shutil.copy2(scaler_path, versioned_scaler_path)

            version_metadata = {
                "version_id": version_id,
                "timestamp": timestamp.isoformat(),
                "model_path": str(versioned_model_path),
                "scaler_path": str(versioned_scaler_path),
                "metrics": metrics,
                "training_info": training_info
            }

            metadata = self._load_metadata()
            metadata["versions"].append(version_metadata)
            metadata["versions"].sort(key=lambda v: v["timestamp"], reverse=True)

            if len(metadata["versions"]) > self.max_versions:
                for old_version in metadata["versions"][self.max_versions:]:
                    old_dir = Path(old_version["model_path"]).parent
                    if old_dir.exists():
                        shutil.rmtree(old_dir)
                        logger.info(f"Deleted version {old_version['version_id']}")

                metadata["versions"] = metadata["versions"][:self.max_versions]

            if metadata["versions"]:
                metadata["latest_version"] = metadata["versions"][0]["version_id"]

            self._save_metadata(metadata)
            logger.info(f"Saved version {version_id}, total: {len(metadata['versions'])}")

            return version_metadata

        except Exception as e:
            logger.error(f"Failed to save version: {str(e)}")
            raise

    # Get the latest model version
    def get_latest_version(self):
        metadata = self._load_metadata()
        return metadata["versions"][0] if metadata["versions"] else None

    # List all model versions
    def list_versions(self):
        return self._load_metadata()["versions"]

    # Get a summary of all model versions
    def get_version_summary(self):
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
