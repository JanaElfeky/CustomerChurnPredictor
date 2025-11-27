from flask import Blueprint, request, jsonify
import pandas as pd
import logging
from app.services.model_interface import predict, retrain_model
from app.models import Customer, Prediction
from app import db

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

        # Extract prediction results
        prediction_value = result['predictions'][0] if 'predictions' in result else None
        probability_value = result['probabilities'][0] if 'probabilities' in result else None

        if prediction_value is None or probability_value is None:
            return jsonify({
                'success': False,
                'error': 'Invalid prediction result'
            }), 500

        # Create or update customer record
        customer = Customer(**data)
        db.session.add(customer)
        db.session.flush()  # Get the customer ID without committing

        # Create prediction record
        prediction_record = Prediction(
            customer_id=customer.id,
            churn_probability=float(probability_value),
            predicted_churn=bool(prediction_value)
        )
        db.session.add(prediction_record)
        db.session.commit()

        # Convert to lists for JSON response
        if 'predictions' in result:
            result['predictions'] = result['predictions'].tolist()
        if 'probabilities' in result:
            result['probabilities'] = result['probabilities'].tolist()

        return jsonify({
            'success': True,
            'customer_id': customer.id,
            'prediction_id': prediction_record.id,
            'prediction': result
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Prediction error: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'error': 'Prediction failed', 'message': str(e)}), 500