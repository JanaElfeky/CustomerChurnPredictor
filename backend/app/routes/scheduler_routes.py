from flask import Blueprint, jsonify
import logging
from app.services.scheduler_service import get_scheduler
from app.services.data_export import get_labeled_data_stats

logger = logging.getLogger(__name__)
scheduler_bp = Blueprint('scheduler', __name__, url_prefix='/api/scheduler')


@scheduler_bp.route('/status', methods=['GET'])
def get_status():
    """
    Get the current status of the retraining scheduler. For debugging
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
        logger.error(
            f"Error getting scheduler status: {
                str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to get scheduler status',
            'message': str(e)
        }), 500
