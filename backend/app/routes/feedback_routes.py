from flask import Blueprint, request, jsonify
import logging
from app.models import Customer, CustomerLabel
from app import db

logger = logging.getLogger(__name__)
feedback_bp = Blueprint('feedback', __name__, url_prefix='/api/feedback')


@feedback_bp.route('/add-label', methods=['POST'])
def add_label():
    """
    Add true outcome label to unlabelled customer data.

    Expected JSON body:
    {
        "customer_id": int,
        "target": bool (true for churned, false for not churned)
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        customer_id = data.get('customer_id')
        target = data.get('target')

        # Validate input
        if customer_id is None:
            return jsonify({'success': False, 'error': 'customer_id is required'}), 400

        if target is None:
            return jsonify({'success': False, 'error': 'target is required'}), 400

        if not isinstance(target, bool):
            return jsonify({'success': False, 'error': 'target must be a boolean'}), 400

        # Check if customer exists
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({
                'success': False,
                'error': f'Customer with id {customer_id} not found'
            }), 404

        # Check if label already exists
        existing_label = CustomerLabel.query.get(customer_id)
        if existing_label:
            # Update existing label
            existing_label.target = target
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Label updated successfully',
                'customer_id': customer_id,
                'target': target,
                'updated': True
            }), 200
        else:
            # Create new label
            new_label = CustomerLabel(
                id=customer_id,
                target=target
            )
            db.session.add(new_label)
            db.session.commit()

            return jsonify({
                'success': True,
                'message': 'Label added successfully',
                'customer_id': customer_id,
                'target': target,
                'updated': False
            }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Feedback label error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to add label',
            'message': str(e)
        }), 500


@feedback_bp.route('/batch-labels', methods=['POST'])
def add_batch_labels():
    """
    Add multiple true outcome labels in batch.

    Expected JSON body:
    {
        "labels": [
            {"customer_id": int, "target": bool},
            {"customer_id": int, "target": bool},
            ...
        ]
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400

        labels = data.get('labels')
        if not labels or not isinstance(labels, list):
            return jsonify({'success': False, 'error': 'labels must be a non-empty list'}), 400

        added = 0
        updated = 0
        errors = []

        for idx, label_data in enumerate(labels):
            customer_id = label_data.get('customer_id')
            target = label_data.get('target')

            # Validate each entry
            if customer_id is None or target is None:
                errors.append({
                    'index': idx,
                    'error': 'Missing customer_id or target'
                })
                continue

            if not isinstance(target, bool):
                errors.append({
                    'index': idx,
                    'customer_id': customer_id,
                    'error': 'target must be a boolean'
                })
                continue

            # Check if customer exists
            customer = Customer.query.get(customer_id)
            if not customer:
                errors.append({
                    'index': idx,
                    'customer_id': customer_id,
                    'error': 'Customer not found'
                })
                continue

            # Check if label already exists
            existing_label = CustomerLabel.query.get(customer_id)
            if existing_label:
                existing_label.target = target
                updated += 1
            else:
                new_label = CustomerLabel(
                    id=customer_id,
                    target=target
                )
                db.session.add(new_label)
                added += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Processed {added + updated} labels',
            'added': added,
            'updated': updated,
            'errors': errors
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Batch feedback error: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': 'Failed to process batch labels',
            'message': str(e)
        }), 500
