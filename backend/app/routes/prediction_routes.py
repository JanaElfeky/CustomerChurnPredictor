from unittest import result
from flask import Blueprint, request, jsonify
import pandas as pd
import logging
from app.services.model_interface import predict, retrain_model
from app.models import Customer

logger = logging.getLogger(__name__)
prediction_bp = Blueprint('prediction', __name__, url_prefix='/api/prediction')


@prediction_bp.route('/single', methods=['POST'])
def predict_single():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        # Convert single record dict to DataFrame
        input_df = pd.DataFrame([data])

        # Call your model interface predict function
        result = predict(input_df)

        if 'predictions' in result:
            result['predictions'] = result['predictions'].tolist()
        if 'probabilities' in result:
            result['probabilities'] = result['probabilities'].tolist()

        return jsonify({'success': True, 'prediction': result}), 200

    except Exception as e:
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Prediction failed', 'message': str(e)}), 500

# @prediction_bp.route('/retrain', methods=['POST'])
# def retrain():
#     try:
#         data = request.get_json()
#         csv_path = data.get('csv_path')
#         if not csv_path:
#             return jsonify({'success': False, 'error': 'Missing csv_path parameter'}), 400

#         # Call your retrain_model function
#         result = retrain_model(csv_path)

#         return jsonify({'success': True, 'metrics': result['final_metrics']}), 200

#     except Exception as e:
#         logger.error(f"Retraining error: {str(e)}", exc_info=True)
#         return jsonify({'success': False, 'error': 'Retraining failed', 'message': str(e)}), 500


# @prediction_bp.route('/customer/<int:customer_id>', methods=['GET'])
# def predict_for_customer(customer_id):
#     try:
#         customer = Customer.query.get(customer_id)
#         if not customer:
#             return jsonify({'success': False, 'error': 'Customer not found'}), 404

#         # Convert customer ORM object to dict and DataFrame for prediction
#         customer_data = {c.name: getattr(customer, c.name) for c in customer.__table__.columns if c.name != 'id'}
#         input_df = pd.DataFrame([customer_data])

#         result = predict(input_df)

#         return jsonify({'success': True, 'customer_id': customer_id, 'prediction': result}), 200

#     except Exception as e:
#         logger.error(f"Customer prediction error: {str(e)}", exc_info=True)
#         return jsonify({'success': False, 'error': 'Prediction failed', 'message': str(e)}), 500
