import os
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.model_interface import retrain_model, MODEL_PATH, SCALER_PATH, ML_MODELS_DIR
from app.services.data_export import export_labeled_data_to_csv, get_labeled_data_stats
from app.services.model_versioning import ModelVersionManager

logger = logging.getLogger(__name__)


class IntegratedRetrainingScheduler:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.last_training_time = None
        self.training_count = 0
        self.enabled = False
        self.app = None
        self.version_manager = None

    # Main retraining job - exports data from DB and retrains model
    def retrain_job(self):
        if not self.app:
            logger.error("Flask app not initialized")
            return

        logger.info(f"Starting retraining #{self.training_count + 1}")

        try:
            with self.app.app_context():
                stats = get_labeled_data_stats()
                logger.info(f"Database stats: {stats}")

                if stats['total_labels'] == 0:
                    logger.warning("No labeled data found")
                    return

                # Create CSV path for training data
                training_data_dir = os.path.join(os.path.dirname(MODEL_PATH), 'training_datasets')
                os.makedirs(training_data_dir, exist_ok=True)
                temp_csv = os.path.join(
                    training_data_dir,
                    f"training_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                )

                # Export new data since last training (or all if first training)
                if self.last_training_time is None:
                    logger.info("First training: exporting all data")
                    export_stats = export_labeled_data_to_csv(temp_csv, include_all=True)
                else:
                    logger.info(f"Exporting data since: {self.last_training_time}")
                    export_stats = export_labeled_data_to_csv(
                        temp_csv,
                        since=self.last_training_time,
                        include_all=False
                    )

                if export_stats['total_records'] == 0:
                    logger.warning("No new data since last training")
                    if os.path.exists(temp_csv):
                        os.remove(temp_csv)
                    return

                logger.info(f"Exported {export_stats['total_records']} records")

            # Retrain model (incremental if model exists)
            results = retrain_model(
                new_data_path=temp_csv,
                target_column='TARGET',
                load_existing=os.path.exists(MODEL_PATH),
                validation_split=0.2,
                epochs=100,
                batch_size=64,
                patience=15,
                verbose=1
            )

            # Save version using ModelVersionManager
            if self.version_manager:
                try:
                    training_info = {
                        "total_samples": export_stats.get('total_records', 0),
                        "churned": export_stats.get('churned', 0),
                        "not_churned": export_stats.get('not_churned', 0),
                        "training_mode": "initial" if self.last_training_time is None else "incremental",
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
                    logger.warning(f"Failed to save version: {str(e)}")

            # Update tracking after successful training
            self.last_training_time = datetime.utcnow()
            self.training_count += 1

            logger.info("Retraining completed")
            for metric, value in results['final_metrics'].items():
                logger.info(f"  {metric}: {value:.4f}")

            # Log available versions
            if self.version_manager:
                versions = self.version_manager.get_version_summary()
                logger.info(f"Available versions: {len(versions)}")
                for v in versions:
                    acc = v['accuracy'] if v['accuracy'] is not None else 0.0
                    auc = v['auc'] if v['auc'] is not None else 0.0
                    logger.info(f"  {v['version_id']}: acc={acc:.4f}, auc={auc:.4f}")

        except Exception as e:
            logger.error(f"Retraining failed: {str(e)}", exc_info=True)

    # Start background scheduler
    def start(self, interval_hours=24):
        if self.enabled:
            logger.warning("Scheduler already running")
            return

        logger.info(f"Starting scheduler (interval: {interval_hours}h)")

        self.scheduler.add_job(
            self.retrain_job,
            'interval',
            hours=interval_hours,
            id='retrain_job',
            replace_existing=True
        )

        self.scheduler.start()
        self.enabled = True

    # Stop scheduler
    def stop(self):
        if self.enabled and self.scheduler.running:
            self.scheduler.shutdown()
            self.enabled = False
            logger.info("Scheduler stopped")

    # Get scheduler status (for API endpoint)
    def get_status(self):
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


# Get or create singleton scheduler
def get_scheduler():
    global _scheduler
    if _scheduler is None:
        _scheduler = IntegratedRetrainingScheduler()
    return _scheduler


# Initialize scheduler with Flask app (called from app/__init__.py)
def init_scheduler(app):
    enable_scheduler = app.config.get('ENABLE_SCHEDULER', False)
    interval_hours = app.config.get('RETRAINING_INTERVAL_HOURS', 24)

    if not enable_scheduler:
        logger.info("Scheduler disabled")
        return

    scheduler = get_scheduler()
    scheduler.app = app

    # Setup model versioning (keeps 3 versions)
    scheduler.version_manager = ModelVersionManager(ML_MODELS_DIR, max_versions=3)
    logger.info("Model versioning enabled")

    # Restore state from latest version
    latest_version = scheduler.version_manager.get_latest_version()
    if latest_version:
        try:
            scheduler.last_training_time = datetime.fromisoformat(latest_version['timestamp'])
            scheduler.training_count = len(scheduler.version_manager.list_versions())
            logger.info(f"Restored training state: {scheduler.training_count} versions")
        except Exception as e:
            logger.warning(f"Could not restore state: {e}")

    # Start scheduler on first request
    @app.before_request
    def start_scheduler_once():
        if not scheduler.enabled:
            with app.app_context():
                scheduler.start(interval_hours=interval_hours)

    # Stop on shutdown
    import atexit
    atexit.register(lambda: scheduler.stop())
