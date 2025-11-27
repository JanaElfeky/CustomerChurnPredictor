"""
Service for exporting labeled customer data from database to CSV for model retraining.
"""

import pandas as pd
import logging
from datetime import datetime
from typing import Optional
from app.models import Customer, CustomerLabel
from app import db

logger = logging.getLogger(__name__)


def export_labeled_data_to_csv(
    output_path: str,
    since: Optional[datetime] = None,
    include_all: bool = False
) -> dict:
    """
    Export labeled customer data from database to CSV file for model retraining.

    Args:
        output_path (str): Path where CSV file will be saved
        since (datetime, optional): Only include labels created/updated after this time
        include_all (bool): If True, include all labeled data regardless of 'since' parameter

    Returns:
        dict: Statistics about the export

    Raises:
        ValueError: If no labeled data is found
    """
    try:
        # Build query to get customers with labels
        query = db.session.query(Customer, CustomerLabel).join(
            CustomerLabel,
            Customer.id == CustomerLabel.id
        )

        # Apply time filter if specified and not include_all
        if since is not None and not include_all:
            query = query.filter(
                db.or_(
                    CustomerLabel.created_at >= since,
                    CustomerLabel.updated_at >= since
                )
            )

        # Execute query
        results = query.all()

        if not results:
            # Return empty stats if no data found (especially for incremental queries)
            if not include_all:
                # For incremental queries, this is normal - no new data
                return {
                    'total_records': 0,
                    'churned': 0,
                    'not_churned': 0,
                    'output_path': output_path
                }
            else:
                # For full data queries, this is an error
                raise ValueError("No labeled customer data found in database")

        # Convert to list of dictionaries
        data_rows = []
        for customer, label in results:
            row = {
                'id': customer.id,
                'amount_rub_clo_prc': customer.amount_rub_clo_prc,
                'sum_tran_aut_tendency3m': customer.sum_tran_aut_tendency3m,
                'cnt_tran_aut_tendency3m': customer.cnt_tran_aut_tendency3m,
                'rest_avg_cur': customer.rest_avg_cur,
                'cr_prod_cnt_tovr': customer.cr_prod_cnt_tovr,
                'trans_count_atm_prc': customer.trans_count_atm_prc,
                'amount_rub_atm_prc': customer.amount_rub_atm_prc,
                'age': customer.age,
                'cnt_tran_med_tendency3m': customer.cnt_tran_med_tendency3m,
                'sum_tran_med_tendency3m': customer.sum_tran_med_tendency3m,
                'sum_tran_clo_tendency3m': customer.sum_tran_clo_tendency3m,
                'cnt_tran_clo_tendency3m': customer.cnt_tran_clo_tendency3m,
                'cnt_tran_sup_tendency3m': customer.cnt_tran_sup_tendency3m,
                'turnover_dynamic_cur_1m': customer.turnover_dynamic_cur_1m,
                'rest_dynamic_paym_3m': customer.rest_dynamic_paym_3m,
                'sum_tran_sup_tendency3m': customer.sum_tran_sup_tendency3m,
                'sum_tran_atm_tendency3m': customer.sum_tran_atm_tendency3m,
                'sum_tran_sup_tendency1m': customer.sum_tran_sup_tendency1m,
                'sum_tran_atm_tendency1m': customer.sum_tran_atm_tendency1m,
                'cnt_tran_sup_tendency1m': customer.cnt_tran_sup_tendency1m,
                'turnover_dynamic_cur_3m': customer.turnover_dynamic_cur_3m,
                'clnt_setup_tenor': customer.clnt_setup_tenor,
                'turnover_dynamic_paym_3m': customer.turnover_dynamic_paym_3m,
                'turnover_dynamic_paym_1m': customer.turnover_dynamic_paym_1m,
                'trans_amount_tendency3m': customer.trans_amount_tendency3m,
                'trans_cnt_tendency3m': customer.trans_cnt_tendency3m,
                'pack_102': customer.pack_102,
                'pack_103': customer.pack_103,
                'pack_104': customer.pack_104,
                'pack_105': customer.pack_105,
                'TARGET': int(label.target),  # Convert boolean to 0/1
            }
            data_rows.append(row)

        # Create DataFrame and save to CSV
        df = pd.DataFrame(data_rows)
        df.to_csv(output_path, index=False)

        # Calculate statistics
        stats = {
            'total_records': len(data_rows),
            'churned': int(df['TARGET'].sum()),
            'not_churned': len(data_rows) - int(df['TARGET'].sum()),
            'output_path': output_path,
            'export_time': datetime.now().isoformat(),
            'filtered': since is not None and not include_all,
            'filter_since': since.isoformat() if since else None
        }

        logger.info(f"Successfully exported {stats['total_records']} labeled records to {output_path}")
        logger.info(f"Churned: {stats['churned']}, Not churned: {stats['not_churned']}")

        return stats

    except Exception as e:
        logger.error(f"Error exporting labeled data: {str(e)}", exc_info=True)
        raise


def get_labeled_data_stats() -> dict:
    """
    Get statistics about labeled data in the database.

    Returns:
        dict: Statistics including total count, churn distribution, and timestamps
    """
    try:
        total_labels = CustomerLabel.query.count()

        if total_labels == 0:
            return {
                'total_labels': 0,
                'churned': 0,
                'not_churned': 0,
                'oldest_label': None,
                'newest_label': None
            }

        churned_count = CustomerLabel.query.filter_by(target=True).count()
        not_churned_count = total_labels - churned_count

        oldest_label = db.session.query(db.func.min(CustomerLabel.created_at)).scalar()
        newest_label = db.session.query(db.func.max(
            db.func.coalesce(CustomerLabel.updated_at, CustomerLabel.created_at)
        )).scalar()

        return {
            'total_labels': total_labels,
            'churned': churned_count,
            'not_churned': not_churned_count,
            'oldest_label': oldest_label.isoformat() if oldest_label else None,
            'newest_label': newest_label.isoformat() if newest_label else None
        }

    except Exception as e:
        logger.error(f"Error getting labeled data stats: {str(e)}", exc_info=True)
        raise
