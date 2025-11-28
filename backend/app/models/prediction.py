from datetime import datetime
from app import db


class Prediction(db.Model):
    __tablename__ = "predictions"

    id = db.Column(db.Integer, db.ForeignKey("customers.id"), primary_key=True, nullable=False)
    churn_probability = db.Column(db.Float, nullable=False)
    predicted_churn = db.Column(db.Boolean, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
