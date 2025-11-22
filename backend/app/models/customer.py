from datetime import datetime
from app import db


class Customer(db.Model):
    __tablename__ = "customers"

    id = db.Column(db.Integer, unique=True, nullable=False,
                   primary_key=True)  # original ID column

    amount_rub_clo_prc = db.Column(db.Float)
    sum_tran_aut_tendency3m = db.Column(db.Float)
    cnt_tran_aut_tendency3m = db.Column(db.Float)
    rest_avg_cur = db.Column(db.Float)
    cr_prod_cnt_tovr = db.Column(db.Float)
    trans_count_atm_prc = db.Column(db.Float)
    amount_rub_atm_prc = db.Column(db.Float)
    age = db.Column(db.Integer)
    cnt_tran_med_tendency3m = db.Column(db.Float)
    sum_tran_med_tendency3m = db.Column(db.Float)
    sum_tran_clo_tendency3m = db.Column(db.Float)
    cnt_tran_clo_tendency3m = db.Column(db.Float)
    cnt_tran_sup_tendency3m = db.Column(db.Float)
    turnover_dynamic_cur_1m = db.Column(db.Float)
    rest_dynamic_paym_3m = db.Column(db.Float)
    sum_tran_sup_tendency3m = db.Column(db.Float)
    sum_tran_atm_tendency3m = db.Column(db.Float)
    sum_tran_sup_tendency1m = db.Column(db.Float)
    sum_tran_atm_tendency1m = db.Column(db.Float)
    cnt_tran_sup_tendency1m = db.Column(db.Float)
    turnover_dynamic_cur_3m = db.Column(db.Float)
    clnt_setup_tenor = db.Column(db.Integer)
    turnover_dynamic_paym_3m = db.Column(db.Float)
    turnover_dynamic_paym_1m = db.Column(db.Float)
    trans_amount_tendency3m = db.Column(db.Float)
    trans_cnt_tendency3m = db.Column(db.Float)

    pack_102 = db.Column(db.Integer)
    pack_103 = db.Column(db.Integer)
    pack_104 = db.Column(db.Integer)
    pack_105 = db.Column(db.Integer)

    labels = db.relationship("CustomerLabel", backref="customer", lazy=True)
