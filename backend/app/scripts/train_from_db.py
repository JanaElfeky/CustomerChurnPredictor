import sys
import os
from datetime import datetime
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from app import create_app, db
from app.models.customer import Customer
from app.models.customer_label import CustomerLabel
from app.services.model_interface import retrain_model, MODEL_PATH, SCALER_PATH, ML_MODELS_DIR
from app.services.model_versioning import ModelVersionManager


def fetch_labeled_customers():
    """
    Fetch all customers that have labels from the database.
    """
    print("Fetching labeled customers from database...")

    # Query customers with labels using a join
    query = db.session.query(Customer, CustomerLabel).join(
        CustomerLabel,
        Customer.id == CustomerLabel.id
    )

    results = query.all()

    if not results:
        raise ValueError("No labeled customers found in database")

    print(f"Found {len(results)} labeled customers")

    # Convert to list of dictionaries
    data = []
    for customer, label in results:
        # Get all customer features
        customer_data = {
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
            # Boolean features (convert to int)
            'pack_102': int(customer.pack_102) if customer.pack_102 is not None else 0,
            'pack_103': int(customer.pack_103) if customer.pack_103 is not None else 0,
            'pack_104': int(customer.pack_104) if customer.pack_104 is not None else 0,
            'pack_105': int(customer.pack_105) if customer.pack_105 is not None else 0,
            # Add target
            'TARGET': int(label.target)
        }
        data.append(customer_data)

    # Create DataFrame
    df = pd.DataFrame(data)

    return df


def save_training_data(df, output_path='training_data_from_db.csv'):
    """
    Save the fetched data to CSV for development
    """
    df.to_csv(output_path, index=False)
    print(f"\nTraining data saved to: {output_path}")


def train_initial_model_from_db(save_csv=True):
    """
    Fetch data from database and train the initial model.
    """

    # Create Flask app context
    app = create_app()

    with app.app_context():
        try:
            # Fetch labeled customers
            df = fetch_labeled_customers()

            # Save to CSV if requested
            if save_csv:
                csv_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    'training_data_from_db.csv'
                )
                save_training_data(df, csv_path)
                temp_data_path = csv_path
            else:
                # Save to temporary file
                import tempfile
                temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv')
                df.to_csv(temp_file.name, index=False)
                temp_data_path = temp_file.name
                temp_file.close()

            print("Starting model training")

            # Train the model
            results = retrain_model(
                new_data_path=temp_data_path,
                target_column='TARGET',
                load_existing=False,  # Train from scratch
                validation_split=0.2,
                epochs=100,
                batch_size=64,
                patience=15,
                verbose=1
            )

            # Clean up temp file if not saving CSV
            if not save_csv and os.path.exists(temp_data_path):
                os.remove(temp_data_path)

            # Save version metadata for scheduler
            try:
                version_manager = ModelVersionManager(ML_MODELS_DIR, max_versions=3)

                # Get data stats
                total_records = len(df)
                churned = int(df['TARGET'].sum())
                not_churned = total_records - churned

                training_info = {
                    "total_samples": total_records,
                    "churned": churned,
                    "not_churned": not_churned,
                    "training_mode": "initial",
                    "is_first_training": True,
                    "epochs": 100,
                    "batch_size": 64
                }

                version_info = version_manager.save_new_version(
                    model_path=results['model_path'],
                    scaler_path=results['scaler_path'],
                    metrics=results['final_metrics'],
                    training_info=training_info
                )
                print(f"\nVersion saved: {version_info['version_id']}")
            except Exception as e:
                print(f"\nCould not save version metadata: {e}")

            return results

        except Exception as e:
            print("MODEL TRAINING FAILED")
            print(f"Error: {str(e)}")
            raise


if __name__ == "__main__":
    # Train the model
    train_initial_model_from_db()
