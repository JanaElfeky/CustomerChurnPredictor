#!/usr/bin/env python3
"""
Automated Testing Script for Customer Churn Prediction API

This script:
1. Generates random but realistic customer data
2. Sends prediction requests to the API
3. Collects the results
4. Sends random feedback labels for testing purposes
"""

import requests
import random
import time
import json
from typing import Dict, List, Any
from datetime import datetime


# Configuration
API_BASE_URL = "http://localhost:5001"
PREDICTION_ENDPOINT = f"{API_BASE_URL}/api/prediction/single"
FEEDBACK_ENDPOINT = f"{API_BASE_URL}/api/feedback/add-label"
BATCH_FEEDBACK_ENDPOINT = f"{API_BASE_URL}/api/feedback/batch-labels"

# Number of customer records to generate
NUM_CUSTOMERS = 20


def generate_realistic_customer() -> Dict[str, Any]:
    """
    Generate a realistic random customer record with valid ranges.

    Returns:
        Dict containing customer features with realistic values
    """
    # Age distribution (skewed towards 25-65)
    age = int(random.triangular(18, 80, 45))

    # Account tenure in months (0-120 months = 0-10 years)
    clnt_setup_tenor = random.randint(1, 120)

    # Rest/balance averages (positive values, realistic banking amounts)
    rest_avg_cur = round(random.uniform(1000, 500000), 2)

    # Transaction counts (non-negative integers as floats)
    cnt_tran_aut_tendency3m = round(random.uniform(0, 100), 2)
    cnt_tran_med_tendency3m = round(random.uniform(0, 50), 2)
    cnt_tran_clo_tendency3m = round(random.uniform(0, 30), 2)
    cnt_tran_sup_tendency3m = round(random.uniform(0, 40), 2)
    cnt_tran_sup_tendency1m = round(random.uniform(0, 15), 2)

    # Transaction sums (positive amounts)
    sum_tran_aut_tendency3m = round(random.uniform(1000, 100000), 2)
    sum_tran_med_tendency3m = round(random.uniform(500, 50000), 2)
    sum_tran_clo_tendency3m = round(random.uniform(500, 30000), 2)
    sum_tran_sup_tendency3m = round(random.uniform(1000, 80000), 2)
    sum_tran_sup_tendency1m = round(random.uniform(300, 30000), 2)
    sum_tran_atm_tendency3m = round(random.uniform(500, 40000), 2)
    sum_tran_atm_tendency1m = round(random.uniform(200, 15000), 2)

    # Percentages (0-100 or 0-1 depending on the field)
    amount_rub_clo_prc = round(random.uniform(0, 100), 2)
    trans_count_atm_prc = round(random.uniform(0, 100), 2)
    amount_rub_atm_prc = round(random.uniform(0, 100), 2)

    # Product counts
    cr_prod_cnt_tovr = round(random.uniform(0, 10), 2)

    # Dynamics (can be positive or negative, representing growth/decline)
    turnover_dynamic_cur_1m = round(random.uniform(-50, 50), 2)
    turnover_dynamic_cur_3m = round(random.uniform(-50, 50), 2)
    turnover_dynamic_paym_1m = round(random.uniform(-50, 50), 2)
    turnover_dynamic_paym_3m = round(random.uniform(-50, 50), 2)
    rest_dynamic_paym_3m = round(random.uniform(-50, 50), 2)

    # Tendencies (can be positive or negative)
    trans_amount_tendency3m = round(random.uniform(-30, 30), 2)
    trans_cnt_tendency3m = round(random.uniform(-30, 30), 2)

    # Package flags (boolean) - randomly assign with some probability
    # Most customers have pack_102, fewer have others
    pack_102 = random.random() < 0.7
    pack_103 = random.random() < 0.3
    pack_104 = random.random() < 0.2
    pack_105 = random.random() < 0.15

    return {
        "amount_rub_clo_prc": amount_rub_clo_prc,
        "sum_tran_aut_tendency3m": sum_tran_aut_tendency3m,
        "cnt_tran_aut_tendency3m": cnt_tran_aut_tendency3m,
        "rest_avg_cur": rest_avg_cur,
        "cr_prod_cnt_tovr": cr_prod_cnt_tovr,
        "trans_count_atm_prc": trans_count_atm_prc,
        "amount_rub_atm_prc": amount_rub_atm_prc,
        "age": age,
        "cnt_tran_med_tendency3m": cnt_tran_med_tendency3m,
        "sum_tran_med_tendency3m": sum_tran_med_tendency3m,
        "sum_tran_clo_tendency3m": sum_tran_clo_tendency3m,
        "cnt_tran_clo_tendency3m": cnt_tran_clo_tendency3m,
        "cnt_tran_sup_tendency3m": cnt_tran_sup_tendency3m,
        "turnover_dynamic_cur_1m": turnover_dynamic_cur_1m,
        "rest_dynamic_paym_3m": rest_dynamic_paym_3m,
        "sum_tran_sup_tendency3m": sum_tran_sup_tendency3m,
        "sum_tran_atm_tendency3m": sum_tran_atm_tendency3m,
        "sum_tran_sup_tendency1m": sum_tran_sup_tendency1m,
        "sum_tran_atm_tendency1m": sum_tran_atm_tendency1m,
        "cnt_tran_sup_tendency1m": cnt_tran_sup_tendency1m,
        "turnover_dynamic_cur_3m": turnover_dynamic_cur_3m,
        "clnt_setup_tenor": clnt_setup_tenor,
        "turnover_dynamic_paym_3m": turnover_dynamic_paym_3m,
        "turnover_dynamic_paym_1m": turnover_dynamic_paym_1m,
        "trans_amount_tendency3m": trans_amount_tendency3m,
        "trans_cnt_tendency3m": trans_cnt_tendency3m,
        "pack_102": pack_102,
        "pack_103": pack_103,
        "pack_104": pack_104,
        "pack_105": pack_105
    }


def request_prediction(customer_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a prediction request to the API.

    Args:
        customer_data: Dictionary containing customer features

    Returns:
        API response as dictionary
    """
    try:
        response = requests.post(
            PREDICTION_ENDPOINT,
            json=customer_data,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error making prediction request: {e}")
        return None


def send_feedback(customer_id: int, actual_churn: bool) -> Dict[str, Any]:
    """
    Send feedback (actual outcome) for a customer.

    Args:
        customer_id: ID of the customer
        actual_churn: True if customer actually churned, False otherwise

    Returns:
        API response as dictionary
    """
    try:
        response = requests.post(
            FEEDBACK_ENDPOINT,
            json={
                "customer_id": customer_id,
                "target": actual_churn
            },
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending feedback: {e}")
        return None


def send_batch_feedback(labels: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Send batch feedback for multiple customers.

    Args:
        labels: List of dictionaries with customer_id and target

    Returns:
        API response as dictionary
    """
    try:
        response = requests.post(
            BATCH_FEEDBACK_ENDPOINT,
            json={"labels": labels},
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending batch feedback: {e}")
        return None


def main():
    """Main execution function."""
    print("=" * 80)
    print("Customer Churn Prediction API - Automated Testing Script")
    print("=" * 80)
    print(f"\nStarting at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Base URL: {API_BASE_URL}")
    print(f"Number of customers to generate: {NUM_CUSTOMERS}\n")

    results = []
    feedback_labels = []

    # Step 1: Generate customers and request predictions
    print("Step 1: Generating customers and requesting predictions...")
    print("-" * 80)

    for i in range(NUM_CUSTOMERS):
        print(f"\n[{i+1}/{NUM_CUSTOMERS}] Generating customer...")

        # Generate random customer
        customer_data = generate_realistic_customer()

        # Request prediction
        print(f"  → Requesting prediction...")
        prediction_result = request_prediction(customer_data)

        if prediction_result and prediction_result.get('success'):
            customer_id = prediction_result.get('customer_id')
            prediction_id = prediction_result.get('prediction_id')
            prediction = prediction_result.get('prediction', {})
            predicted_churn = prediction.get('predictions', [None])[0]
            churn_probability = prediction.get('probabilities', [None])[0]

            print(f"  ✓ Prediction successful!")
            print(f"    Customer ID: {customer_id}")
            print(f"    Prediction ID: {prediction_id}")
            print(f"    Predicted Churn: {predicted_churn}")
            print(f"    Churn Probability: {churn_probability:.2%}" if churn_probability else "    Churn Probability: N/A")

            # Store result
            results.append({
                'customer_id': customer_id,
                'prediction_id': prediction_id,
                'customer_data': customer_data,
                'predicted_churn': predicted_churn,
                'churn_probability': churn_probability
            })

            # Generate random actual outcome for feedback
            # Use probability-weighted randomness for more realistic simulation
            random_outcome = random.random() < 0.3  # 30% base churn rate

            feedback_labels.append({
                'customer_id': customer_id,
                'target': random_outcome
            })
        else:
            print(f"  ✗ Prediction failed!")
            if prediction_result:
                print(f"    Error: {prediction_result.get('error', 'Unknown error')}")

        # Small delay to avoid overwhelming the server
        time.sleep(0.5)

    # Step 2: Send feedback
    print("\n" + "=" * 80)
    print(f"Step 2: Sending feedback for {len(feedback_labels)} customers...")
    print("-" * 80)

    if feedback_labels:
        # Option 1: Send batch feedback (more efficient)
        print("\nSending batch feedback...")
        batch_result = send_batch_feedback(feedback_labels)

        if batch_result and batch_result.get('success'):
            print(f"✓ Batch feedback successful!")
            print(f"  Added: {batch_result.get('added', 0)}")
            print(f"  Updated: {batch_result.get('updated', 0)}")
            if batch_result.get('errors'):
                print(f"  Errors: {len(batch_result.get('errors', []))}")
        else:
            print(f"✗ Batch feedback failed!")
            if batch_result:
                print(f"  Error: {batch_result.get('error', 'Unknown error')}")

    # Step 3: Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Total customers processed: {len(results)}")
    print(f"Total feedback submitted: {len(feedback_labels)}")

    if results:
        # Statistics
        churned_predictions = sum(1 for r in results if r['predicted_churn'])
        churned_actual = sum(1 for f in feedback_labels if f['target'])
        avg_probability = sum(r['churn_probability'] for r in results if r['churn_probability']) / len(results)

        print(f"\nPrediction Statistics:")
        print(f"  Predicted to churn: {churned_predictions} ({churned_predictions/len(results)*100:.1f}%)")
        print(f"  Average churn probability: {avg_probability:.2%}")

        print(f"\nFeedback Statistics:")
        print(f"  Actually churned (random): {churned_actual} ({churned_actual/len(feedback_labels)*100:.1f}%)")
        print(f"  Did not churn (random): {len(feedback_labels) - churned_actual} ({(len(feedback_labels) - churned_actual)/len(feedback_labels)*100:.1f}%)")

    print(f"\nCompleted at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Optional: Save results to file
    output_file = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'num_customers': NUM_CUSTOMERS,
            'results': results,
            'feedback': feedback_labels
        }, f, indent=2)
    print(f"\n📁 Results saved to: {output_file}")


if __name__ == "__main__":
    main()
