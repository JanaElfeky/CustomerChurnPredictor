from flask import Blueprint, jsonify, request
import logging
from app.models import Prediction

logger = logging.getLogger(__name__)
history_bp = Blueprint('history', __name__, url_prefix='/api/history')

@history_bp.route('/recent', methods=['GET'])
def get_recent_predictions():
    try:
        # Get limit from query parameters, default to 20, max 50
        limit = request.args.get('limit', default=20, type=int)
        limit = max(1, min(limit, 50))

        # Query the most recent N predictions
        predictions = Prediction.query.order_by(
            Prediction.created_at.desc()).limit(limit).all()

        # Convert predictions to list of dicts
        recent_history = [{
            'id': pred.id,
            'customer_id': pred.id,
            'churn_probability': pred.churn_probability,
            'predicted_churn': pred.predicted_churn,
            'created_at': pred.created_at.isoformat() if pred.created_at else None
        } for pred in predictions]

        return jsonify({
            'success': True,
            'count': len(recent_history),
            'predictions': recent_history
        }), 200

    except Exception as e:
        logger.error(
            f"Recent history retrieval error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve recent prediction history',
            'message': str(e)
        }), 500
