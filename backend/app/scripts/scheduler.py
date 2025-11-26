"""
Scheduler for automated model retraining at set intervals.
This script runs continuously and retrains the model at specified intervals.
"""

import sys
import os
import time
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.app.services.model_interface import retrain_model, MODEL_PATH, SCALER_PATH

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('retraining_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ModelRetrainingScheduler:
    """
    Scheduler for automated model retraining.
    """

    def __init__(self, data_path, target_column='TARGET'):
        """
        Initialize the scheduler.

        Args:
            data_path (str): Path to the labeled data CSV for retraining
            target_column (str): Name of the target column
        """
        self.data_path = data_path
        self.target_column = target_column
        self.scheduler = BackgroundScheduler()
        self.last_training_time = None
        self.training_count = 0

    def retrain_job(self):
        """
        Job that runs the retraining process.
        """
        logger.info("=" * 70)
        logger.info("SCHEDULED RETRAINING STARTED")
        logger.info("=" * 70)
        logger.info(f"Training count: {self.training_count + 1}")
        logger.info(f"Data path: {self.data_path}")

        try:
            # Check if data file exists
            if not os.path.exists(self.data_path):
                logger.error(f"Data file not found at {self.data_path}")
                return

            # Retrain the model
            results = retrain_model(
                new_data_path=self.data_path,
                target_column=self.target_column,
                load_existing=os.path.exists(MODEL_PATH),
                validation_split=0.2,
                epochs=100,
                batch_size=64,
                patience=15,
                verbose=1
            )

            # Update tracking
            self.last_training_time = datetime.now()
            self.training_count += 1

            logger.info("=" * 70)
            logger.info("SCHEDULED RETRAINING COMPLETED SUCCESSFULLY")
            logger.info("=" * 70)
            logger.info(f"Model saved to: {results['model_path']}")
            logger.info(f"Scaler saved to: {results['scaler_path']}")
            logger.info(f"Final metrics:")
            for metric, value in results['final_metrics'].items():
                logger.info(f"  {metric}: {value:.4f}")
            logger.info(f"Total trainings completed: {self.training_count}")

        except Exception as e:
            logger.error("=" * 70)
            logger.error("SCHEDULED RETRAINING FAILED")
            logger.error("=" * 70)
            logger.error(f"Error: {str(e)}", exc_info=True)

    def start_interval_schedule(self, interval_hours=24):
        """
        Start the scheduler with an interval-based trigger.

        Args:
            interval_hours (int): Hours between retraining runs
        """
        logger.info(f"Starting scheduler with {interval_hours}-hour interval")

        self.scheduler.add_job(
            self.retrain_job,
            'interval',
            hours=interval_hours,
            id='retrain_job',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info(f"Scheduler started. Model will retrain every {interval_hours} hours")
        logger.info(f"Press Ctrl+C to stop")

    def start_cron_schedule(self, cron_expression):
        """
        Start the scheduler with a cron-based trigger.

        Args:
            cron_expression (str): Cron expression (e.g., "0 2 * * *" for daily at 2 AM)
        """
        logger.info(f"Starting scheduler with cron expression: {cron_expression}")

        self.scheduler.add_job(
            self.retrain_job,
            CronTrigger.from_crontab(cron_expression),
            id='retrain_job',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info(f"Scheduler started with cron: {cron_expression}")
        logger.info(f"Press Ctrl+C to stop")

    def start_daily_schedule(self, hour=2, minute=0):
        """
        Start the scheduler to run daily at a specific time.

        Args:
            hour (int): Hour of day (0-23)
            minute (int): Minute of hour (0-59)
        """
        logger.info(f"Starting scheduler for daily retraining at {hour:02d}:{minute:02d}")

        self.scheduler.add_job(
            self.retrain_job,
            'cron',
            hour=hour,
            minute=minute,
            id='retrain_job',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info(f"Scheduler started. Model will retrain daily at {hour:02d}:{minute:02d}")
        logger.info(f"Press Ctrl+C to stop")

    def run_now_and_schedule(self, interval_hours=24):
        """
        Run retraining immediately and then start interval schedule.

        Args:
            interval_hours (int): Hours between retraining runs
        """
        logger.info("Running initial retraining now...")
        self.retrain_job()
        self.start_interval_schedule(interval_hours)

    def stop(self):
        """Stop the scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler stopped")

    def get_status(self):
        """Get status information about the scheduler."""
        status = {
            'running': self.scheduler.running,
            'training_count': self.training_count,
            'last_training_time': self.last_training_time.isoformat() if self.last_training_time else None,
            'next_run_time': None
        }

        if self.scheduler.running:
            jobs = self.scheduler.get_jobs()
            if jobs:
                status['next_run_time'] = jobs[0].next_run_time.isoformat() if jobs[0].next_run_time else None

        return status


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Automated model retraining scheduler')
    parser.add_argument('data_path', type=str, help='Path to the labeled training data CSV file')
    parser.add_argument('--target', type=str, default='TARGET', help='Name of the target column (default: TARGET)')
    parser.add_argument('--interval', type=int, help='Retrain every N hours')
    parser.add_argument('--daily', type=str, help='Retrain daily at specific time (format: HH:MM, e.g., 02:00)')
    parser.add_argument('--cron', type=str, help='Cron expression for custom schedule (e.g., "0 2 * * *")')
    parser.add_argument('--run-now', action='store_true', help='Run retraining immediately before starting schedule')

    args = parser.parse_args()

    # Validate arguments
    if not os.path.exists(args.data_path):
        print(f"Error: Data file not found at {args.data_path}")
        sys.exit(1)

    schedule_count = sum([args.interval is not None, args.daily is not None, args.cron is not None])
    if schedule_count == 0:
        print("Error: You must specify at least one scheduling option (--interval, --daily, or --cron)")
        sys.exit(1)
    elif schedule_count > 1:
        print("Error: You can only specify one scheduling option")
        sys.exit(1)

    # Create scheduler
    scheduler = ModelRetrainingScheduler(args.data_path, args.target)

    try:
        # Start appropriate schedule
        if args.interval:
            if args.run_now:
                scheduler.run_now_and_schedule(args.interval)
            else:
                scheduler.start_interval_schedule(args.interval)
        elif args.daily:
            try:
                hour, minute = map(int, args.daily.split(':'))
                scheduler.start_daily_schedule(hour, minute)
            except ValueError:
                print("Error: Invalid time format. Use HH:MM (e.g., 02:00)")
                sys.exit(1)
        elif args.cron:
            scheduler.start_cron_schedule(args.cron)

        # Keep running
        while True:
            time.sleep(1)

    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutdown requested...")
        scheduler.stop()
        logger.info("Scheduler shut down successfully")
