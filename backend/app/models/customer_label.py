from datetime import datetime
from app import db


class CustomerLabel(db.Model):
    __tablename__ = "customer_labels"

    id = db.Column(
        db.Integer,
        db.ForeignKey("customers.id"),
        primary_key=True,
        nullable=False)
    target = db.Column(db.Boolean, nullable=False)  # 0/1
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
