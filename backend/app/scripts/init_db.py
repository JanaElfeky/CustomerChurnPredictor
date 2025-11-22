import os
import pandas as pd

from app import create_app, db
from app.models import Customer, CustomerLabel


def init_db_from_csv(csv_path: str):
    app = create_app()
    with app.app_context():
        # Create tables
        db.create_all()

        # Load training dataset
        df = pd.read_csv(csv_path)

        # Iterate rows and insert
        for _, row in df.iterrows():
            customer = Customer(
                id=int(row["ID"]),  # Use ID as PK directly
                amount_rub_clo_prc=row["AMOUNT_RUB_CLO_PRC"],
                sum_tran_aut_tendency3m=row["SUM_TRAN_AUT_TENDENCY3M"],
                cnt_tran_aut_tendency3m=row["CNT_TRAN_AUT_TENDENCY3M"],
                rest_avg_cur=row["REST_AVG_CUR"],
                cr_prod_cnt_tovr=row["CR_PROD_CNT_TOVR"],
                trans_count_atm_prc=row["TRANS_COUNT_ATM_PRC"],
                amount_rub_atm_prc=row["AMOUNT_RUB_ATM_PRC"],
                age=int(row["AGE"]),
                cnt_tran_med_tendency3m=row["CNT_TRAN_MED_TENDENCY3M"],
                sum_tran_med_tendency3m=row["SUM_TRAN_MED_TENDENCY3M"],
                sum_tran_clo_tendency3m=row["SUM_TRAN_CLO_TENDENCY3M"],
                cnt_tran_clo_tendency3m=row["CNT_TRAN_CLO_TENDENCY3M"],
                cnt_tran_sup_tendency3m=row["CNT_TRAN_SUP_TENDENCY3M"],
                turnover_dynamic_cur_1m=row["TURNOVER_DYNAMIC_CUR_1M"],
                rest_dynamic_paym_3m=row["REST_DYNAMIC_PAYM_3M"],
                sum_tran_sup_tendency3m=row["SUM_TRAN_SUP_TENDENCY3M"],
                sum_tran_atm_tendency3m=row["SUM_TRAN_ATM_TENDENCY3M"],
                sum_tran_sup_tendency1m=row["SUM_TRAN_SUP_TENDENCY1M"],
                sum_tran_atm_tendency1m=row["SUM_TRAN_ATM_TENDENCY1M"],
                cnt_tran_sup_tendency1m=row["CNT_TRAN_SUP_TENDENCY1M"],
                turnover_dynamic_cur_3m=row["TURNOVER_DYNAMIC_CUR_3M"],
                clnt_setup_tenor=int(row["CLNT_SETUP_TENOR"]),
                turnover_dynamic_paym_3m=row["TURNOVER_DYNAMIC_PAYM_3M"],
                turnover_dynamic_paym_1m=row["TURNOVER_DYNAMIC_PAYM_1M"],
                trans_amount_tendency3m=row["TRANS_AMOUNT_TENDENCY3M"],
                trans_cnt_tendency3m=row["TRANS_CNT_TENDENCY3M"],
                pack_102=int(row["PACK_102"]),
                pack_103=int(row["PACK_103"]),
                pack_104=int(row["PACK_104"]),
                pack_105=int(row["PACK_105"]),
            )
            db.session.add(customer)
            db.session.flush()  # important to flush to sync PK for FK use

            # Insert label if TARGET is present
            if "TARGET" in df.columns and not pd.isnull(row["TARGET"]):
                label = CustomerLabel(
                    id=customer.id,  # Use the same ID as PK and FK
                    target=int(row["TARGET"]),
                )
                db.session.add(label)

        db.session.commit()
        print("Database initialized with training data.")


if __name__ == "__main__":
    csv_path = 'churn_data_cleaned.csv'
    init_db_from_csv(csv_path)
