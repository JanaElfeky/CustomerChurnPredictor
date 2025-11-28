from flask import Blueprint, jsonify
import logging
from app.models import Prediction

logger = logging.getLogger(__name__)
history_bp = Blueprint('history', __name__, url_prefix='/api/history')


@history_bp.route('/customer/<int:customer_id>', methods=['GET'])
def get_customer_history(customer_id):
    try:
        # Query all predictions for the specified customer
        predictions = Prediction.query.filter_by(id=customer_id).order_by(Prediction.created_at.desc()).all()

        if not predictions:
            return jsonify({
                'success': True,
                'customer_id': customer_id,
                'predictions': [],
                'message': 'No prediction history found for this customer'
            }), 200

        # Convert predictions to list of dicts
        prediction_history = [{
            'id': pred.id,
            'customer_id': pred.id,
            'churn_probability': pred.churn_probability,
            'predicted_churn': pred.predicted_churn,
            'created_at': pred.created_at.isoformat() if pred.created_at else None
        } for pred in predictions]

        return jsonify({
            'success': True,
            'customer_id': customer_id,
            'count': len(prediction_history),
            'predictions': prediction_history
        }), 200

    except Exception as e:
        logger.error(f"History retrieval error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve prediction history',
            'message': str(e)
        }), 500
        

@history_bp.route('/recent', methods=['GET'])
def get_recent_predictions():
    try:
        # Query the most recent 20 predictions
        predictions = Prediction.query.order_by(Prediction.created_at.desc()).limit(20).all()

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
        logger.error(f"Recent history retrieval error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve recent prediction history',
            'message': str(e)
        }), 500
