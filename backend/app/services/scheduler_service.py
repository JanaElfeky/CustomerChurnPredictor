"""
Integrated scheduler service that runs within the Flask application.
This allows the scheduler to start automatically when the Flask app starts.
"""

import os
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.model_interface import retrain_model, MODEL_PATH, SCALER_PATH, ML_MODELS_DIR
from app.services.data_export import export_labeled_data_to_csv, get_labeled_data_stats
from app.services.model_versioning import ModelVersionManager
from flask import current_app

logger = logging.getLogger(__name__)


class IntegratedRetrainingScheduler:
    """
    Integrated scheduler that runs within Flask application.
    Automatically exports labeled data from database and retrains model.
    """

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.last_training_time = None
        self.training_count = 0
        self.enabled = False
        self.app = None
        self.version_manager = None

    def retrain_job(self):
        """
        Job that runs the retraining process.
        Exports data from database and retrains model.
        """
        if not self.app:
            logger.error("Flask app not initialized in scheduler")
            return

        logger.info("=" * 70)
        logger.info("SCHEDULED RETRAINING STARTED")
        logger.info("=" * 70)
        logger.info(f"Training count: {self.training_count + 1}")

        try:
            # Use Flask app context for database operations
            with self.app.app_context():
                # Log database stats
                stats = get_labeled_data_stats()
                logger.info(f"Database stats: {stats}")

                if stats['total_labels'] == 0:
                    logger.warning("No labeled data found in database. Skipping retraining.")
                    return

                # Generate temporary CSV path
                temp_csv = os.path.join(
                    os.path.dirname(MODEL_PATH),
                    f"training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )

                # Export only new labeled data since last training (incremental)
                if self.last_training_time is None:
                    logger.info("First training: exporting ALL labeled data")
                    export_stats = export_labeled_data_to_csv(
                        output_path=temp_csv,
                        include_all=True
                    )
                else:
                    logger.info(f"Exporting NEW data since last training: {self.last_training_time}")
                    export_stats = export_labeled_data_to_csv(
                        output_path=temp_csv,
                        since=self.last_training_time,
                        include_all=False
                    )

                if export_stats['total_records'] == 0:
                    logger.warning("No new labeled data since last training. Skipping retraining.")
                    # Clean up empty file
                    if os.path.exists(temp_csv):
                        os.remove(temp_csv)
                    return

                logger.info(f"Exported {export_stats['total_records']} records to {temp_csv}")

            # Retrain the model incrementally (continue from previous weights)
            logger.info(f"Retraining model incrementally with data from: {temp_csv}")
            results = retrain_model(
                new_data_path=temp_csv,
                target_column='TARGET',
                load_existing=os.path.exists(MODEL_PATH),  # Load previous weights if available
                validation_split=0.2,
                epochs=100,
                batch_size=64,
                patience=15,
                verbose=1
            )

            # Save model version with metadata
            if self.version_manager:
                try:
                    training_info = {
                        "total_samples": export_stats.get('total_records', 0),
                        "churned": export_stats.get('churned', 0),
                        "not_churned": export_stats.get('not_churned', 0),
                        "training_mode": "initial" if self.last_training_time is None else "incremental",
                        "new_samples_only": self.last_training_time is not None,
                        "epochs": 100,
                        "batch_size": 64
                    }

                    version_info = self.version_manager.save_new_version(
                        model_path=results['model_path'],
                        scaler_path=results['scaler_path'],
                        metrics=results['final_metrics'],
                        training_info=training_info
                    )

                    logger.info(f"Saved as version: {version_info['version_id']}")

                except Exception as e:
                    logger.warning(f"Failed to save model version: {str(e)}")

            # Update tracking AFTER successful training (use UTC to match database timestamps)
            training_completion_time = datetime.utcnow()
            self.last_training_time = training_completion_time
            self.training_count += 1

            # Clean up temporary CSV
            if os.path.exists(temp_csv):
                try:
                    os.remove(temp_csv)
                    logger.info(f"Cleaned up temporary file: {temp_csv}")
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temp file: {cleanup_error}")

            logger.info("=" * 70)
            logger.info("SCHEDULED RETRAINING COMPLETED SUCCESSFULLY")
            logger.info("=" * 70)
            logger.info(f"Model saved to: {results['model_path']}")
            logger.info(f"Scaler saved to: {results['scaler_path']}")
            logger.info(f"Final metrics:")
            for metric, value in results['final_metrics'].items():
                logger.info(f"  {metric}: {value:.4f}")
            logger.info(f"Total trainings completed: {self.training_count}")
            logger.info(f"Next training will use data after: {training_completion_time}")

            # Log version summary
            if self.version_manager:
                versions = self.version_manager.get_version_summary()
                logger.info(f"Available versions: {len(versions)}")
                for v in versions:
                    acc = v['accuracy'] if v['accuracy'] is not None else 0.0
                    auc = v['auc'] if v['auc'] is not None else 0.0
                    logger.info(f"  - {v['version_id']}: acc={acc:.4f}, auc={auc:.4f}")

        except Exception as e:
            logger.error("=" * 70)
            logger.error("SCHEDULED RETRAINING FAILED")
            logger.error("=" * 70)
            logger.error(f"Error: {str(e)}", exc_info=True)

    def start(self, interval_hours=24):
        """
        Start the scheduler with the Flask application.

        Args:
            interval_hours (int): Hours between retraining runs
        """
        if self.enabled:
            logger.warning("Scheduler already running")
            return

        logger.info(f"Starting integrated scheduler with {interval_hours}-hour interval")

        self.scheduler.add_job(
            self.retrain_job,
            'interval',
            hours=interval_hours,
            id='retrain_job',
            replace_existing=True
        )

        self.scheduler.start()
        self.enabled = True
        logger.info(f"Scheduler started. Model will retrain every {interval_hours} hours")

    def stop(self):
        """Stop the scheduler."""
        if self.enabled and self.scheduler.running:
            self.scheduler.shutdown()
            self.enabled = False
            logger.info("Scheduler stopped")

    def get_status(self):
        """Get status information about the scheduler."""
        status = {
            'enabled': self.enabled,
            'running': self.scheduler.running if self.enabled else False,
            'training_count': self.training_count,
            'last_training_time': self.last_training_time.isoformat() if self.last_training_time else None,
            'next_run_time': None
        }

        if self.enabled and self.scheduler.running:
            jobs = self.scheduler.get_jobs()
            if jobs:
                status['next_run_time'] = jobs[0].next_run_time.isoformat() if jobs[0].next_run_time else None

        return status


# Global scheduler instance
_scheduler = None


def get_scheduler():
    """Get or create the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = IntegratedRetrainingScheduler()
    return _scheduler


def init_scheduler(app):
    """
    Initialize the scheduler with the Flask app.
    Call this from create_app() to start automatic retraining.

    Args:
        app: Flask application instance
    """
    # Check if scheduler should be enabled via config
    enable_scheduler = app.config.get('ENABLE_SCHEDULER', False)
    interval_hours = app.config.get('RETRAINING_INTERVAL_HOURS', 24)

    if not enable_scheduler:
        logger.info("Automatic retraining scheduler is DISABLED (set ENABLE_SCHEDULER=True to enable)")
        return

    scheduler = get_scheduler()
    scheduler.app = app  # Set Flask app reference for database context

    # Initialize model version manager
    scheduler.version_manager = ModelVersionManager(ML_MODELS_DIR, max_versions=3)
    logger.info("Model versioning enabled (keeping 3 most recent versions)")

    # Restore last_training_time from latest model version metadata
    latest_version = scheduler.version_manager.get_latest_version()
    if latest_version:
        try:
            from datetime import datetime
            scheduler.last_training_time = datetime.fromisoformat(latest_version['timestamp'])
            scheduler.training_count = len(scheduler.version_manager.list_versions())
            logger.info(f"Restored last training time from metadata: {scheduler.last_training_time}")
            logger.info(f"Training count restored: {scheduler.training_count}")
        except Exception as e:
            logger.warning(f"Could not restore last training time from metadata: {e}")

    # Start scheduler when app is ready
    @app.before_request
    def start_scheduler_once():
        """Start scheduler on first request."""
        if not scheduler.enabled:
            with app.app_context():
                scheduler.start(interval_hours=interval_hours)

    # Register shutdown handler
    import atexit
    atexit.register(lambda: scheduler.stop())

    logger.info(f"Scheduler initialized. Will start on first request with {interval_hours}h interval")
