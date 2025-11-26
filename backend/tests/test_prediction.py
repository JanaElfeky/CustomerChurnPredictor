"""
Simple test script to predict churn for a single customer record.
"""
import sys
import os
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app.services.model_interface import predict

# Test customer records (using database column names - lowercase)
# Point 1: [146856,0,0.689079823,1,0,1,0.8,0.985536201,31,1,0.794423413,0.795942905,1,1,0,0.117016504,0.627334163,0.001259446,0.212211825,0.001259446,1,0,9.759689553,0.049814651,0.011560847,0.001241229,0.066666667,FALSE,FALSE,FALSE,TRUE]
customer_1 = {
    'id': 146856,
    'amount_rub_clo_prc': 0.0,
    'sum_tran_aut_tendency3m': 0.689079823,
    'cnt_tran_aut_tendency3m': 1.0,
    'rest_avg_cur': 0.0,
    'cr_prod_cnt_tovr': 1.0,
    'trans_count_atm_prc': 0.8,
    'amount_rub_atm_prc': 0.985536201,
    'age': 31,
    'cnt_tran_med_tendency3m': 1.0,
    'sum_tran_med_tendency3m': 0.794423413,
    'sum_tran_clo_tendency3m': 0.795942905,
    'cnt_tran_clo_tendency3m': 1.0,
    'cnt_tran_sup_tendency3m': 1.0,
    'turnover_dynamic_cur_1m': 0.0,
    'rest_dynamic_paym_3m': 0.117016504,
    'sum_tran_sup_tendency3m': 0.627334163,
    'sum_tran_atm_tendency3m': 0.001259446,
    'sum_tran_sup_tendency1m': 0.212211825,
    'sum_tran_atm_tendency1m': 0.001259446,
    'cnt_tran_sup_tendency1m': 1.0,
    'turnover_dynamic_cur_3m': 0.0,
    'clnt_setup_tenor': 9,
    'turnover_dynamic_paym_3m': 0.759689553,
    'turnover_dynamic_paym_1m': 0.049814651,
    'trans_amount_tendency3m': 0.011560847,
    'trans_cnt_tendency3m': 0.001241229,
    'pack_102': False,
    'pack_103': False,
    'pack_104': False,
    'pack_105': True,
}

# Point 2: [146925,0,0.689079823,1,44413.93297,1,0.566037736,0.962548494,44,1,0.794423413,0.795942905,1,1,0.000995891,0,0.627334163,0.039130435,0.212211825,0.203741054,1,0.04363302,2.240872349,0,0,0.041739869,0.264150943,FALSE,FALSE,FALSE,FALSE]
customer_2 = {
    'id': 146925,
    'amount_rub_clo_prc': 0.0,
    'sum_tran_aut_tendency3m': 0.689079823,
    'cnt_tran_aut_tendency3m': 1.0,
    'rest_avg_cur': 44413.93297,
    'cr_prod_cnt_tovr': 1.0,
    'trans_count_atm_prc': 0.566037736,
    'amount_rub_atm_prc': 0.962548494,
    'age': 44,
    'cnt_tran_med_tendency3m': 1.0,
    'sum_tran_med_tendency3m': 0.794423413,
    'sum_tran_clo_tendency3m': 0.795942905,
    'cnt_tran_clo_tendency3m': 1.0,
    'cnt_tran_sup_tendency3m': 1.0,
    'turnover_dynamic_cur_1m': 0.000995891,
    'rest_dynamic_paym_3m': 0.0,
    'sum_tran_sup_tendency3m': 0.627334163,
    'sum_tran_atm_tendency3m': 0.039130435,
    'sum_tran_sup_tendency1m': 0.212211825,
    'sum_tran_atm_tendency1m': 0.203741054,
    'cnt_tran_sup_tendency1m': 1.0,
    'turnover_dynamic_cur_3m': 0.04363302,
    'clnt_setup_tenor': 2,
    'turnover_dynamic_paym_3m': 2.240872349,
    'turnover_dynamic_paym_1m': 0.0,
    'trans_amount_tendency3m': 0.0,
    'trans_cnt_tendency3m': 0.041739869,
    'pack_102': False,
    'pack_103': False,
    'pack_104': False,
    'pack_105': False,
}

# Create DataFrame with both customers
customers_df = pd.DataFrame([customer_1, customer_2])

print("=" * 70)
print("CUSTOMER CHURN PREDICTION TEST - BATCH MODE")
print("=" * 70)
print(f"\nNumber of customers: {len(customers_df)}")
print()

# Display customer info
for idx, customer in enumerate([customer_1, customer_2], 1):
    package = "PACK_105" if customer['pack_105'] else "No Premium Package"
    print(f"Customer {idx} - ID: {customer['id']}, Age: {customer['age']}, Package: {package}")

print()

# Make predictions for both customers
try:
    results = predict(customers_df)

    print("=" * 70)
    print("PREDICTION RESULTS")
    print("=" * 70)

    # Display results for each customer
    for idx in range(len(results['predictions'])):
        customer = customer_1 if idx == 0 else customer_2
        prediction = results['predictions'][idx]
        probability = results['probabilities'][idx]

        print(f"\n{'─' * 70}")
        print(f"CUSTOMER {idx + 1} (ID: {customer['id']})")
        print(f"{'─' * 70}")
        print(f"Age: {customer['age']}")
        print(f"Account Age (clnt_setup_tenor): {customer['clnt_setup_tenor']} months")
        print(f"Average Balance (rest_avg_cur): ${customer['rest_avg_cur']:,.2f}")
        print(f"Package: {'PACK_105 (Premium)' if customer['pack_105'] else 'Standard'}")
        print()
        print(f"Churn Prediction: {'WILL CHURN ⚠️' if prediction == 1 else 'WILL NOT CHURN ✓'}")
        print(f"Churn Probability: {probability:.4f} ({probability*100:.2f}%)")

        # Interpretation
        if probability >= 0.5:
            risk_level = "🔴 HIGH RISK"
            recommendation = "IMMEDIATE ACTION REQUIRED - Contact customer retention team"
        elif probability >= 0.3:
            risk_level = "🟡 MEDIUM RISK"
            recommendation = "Monitor customer - Consider targeted retention offers"
        else:
            risk_level = "🟢 LOW RISK"
            recommendation = "Customer likely to stay - Continue regular engagement"

        print(f"\nRisk Level: {risk_level}")
        print(f"Recommendation: {recommendation}")

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total Customers Analyzed: {len(results['predictions'])}")
    print(f"Predicted to Churn: {sum(results['predictions'])}")
    print(f"Predicted to Stay: {len(results['predictions']) - sum(results['predictions'])}")
    print(f"Average Churn Probability: {sum(results['probabilities'])/len(results['probabilities']):.4f} ({sum(results['probabilities'])/len(results['probabilities'])*100:.2f}%)")
    print("=" * 70)

except FileNotFoundError as e:
    print(f"ERROR: {e}")
    print("\nModel files not found. Please train the model first by running:")
    print("  cd backend && python app/scripts/train_from_db.py")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
