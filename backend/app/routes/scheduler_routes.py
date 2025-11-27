"""
Routes for monitoring and managing the model retraining scheduler.
"""

from flask import Blueprint, jsonify
import logging
from app.services.scheduler_service import get_scheduler
from app.services.data_export import get_labeled_data_stats

logger = logging.getLogger(__name__)
scheduler_bp = Blueprint('scheduler', __name__, url_prefix='/api/scheduler')


@scheduler_bp.route('/status', methods=['GET'])
def get_status():
    """
    Get the current status of the retraining scheduler.

    Returns:
        JSON response with scheduler status including:
        - enabled: Whether scheduler is running
        - training_count: Number of completed training runs
        - last_training_time: When the last training occurred
        - next_run_time: When the next training is scheduled
        - labeled_data_stats: Current database statistics
    """
    try:
        scheduler = get_scheduler()
        status = scheduler.get_status()

        # Also include database stats
        try:
            db_stats = get_labeled_data_stats()
            status['labeled_data_stats'] = db_stats
        except Exception as e:
            logger.warning(f"Could not fetch labeled data stats: {e}")
            status['labeled_data_stats'] = None

        return jsonify({
            'success': True,
            'scheduler': status
        }), 200

    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to get scheduler status',
            'message': str(e)
        }), 500


@scheduler_bp.route('/health', methods=['GET'])
def health_check():
    """
    Simple health check endpoint for the scheduler.

    Returns:
        JSON response indicating if scheduler is operational
    """
    try:
        scheduler = get_scheduler()
        status = scheduler.get_status()

        is_healthy = status['enabled'] and status['running']

        return jsonify({
            'success': True,
            'healthy': is_healthy,
            'enabled': status['enabled'],
            'running': status['running']
        }), 200 if is_healthy else 503

    except Exception as e:
        logger.error(f"Scheduler health check failed: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'healthy': False,
            'error': str(e)
        }), 503
