from app import db
from datetime import datetime

class Payment(db.Model):
    __tablename__ = 'payments'
    payment_id = db.Column(db.Integer, primary_key=True)
    agreement_id = db.Column(db.Integer, db.ForeignKey('rental_agreements.agreement_id'), nullable=False)
    transaction_id = db.Column(db.String(30), unique=True, nullable=False)
    base_amount = db.Column(db.Float, nullable=False)
    deposit_amount = db.Column(db.Float, default=0.0)
    extras_amount = db.Column(db.Float, default=0.0)
    late_fee = db.Column(db.Float, default=0.0)
    fuel_penalty = db.Column(db.Float, default=0.0)
    vat_amount = db.Column(db.Float, default=0.0)
    total_paid = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(20), nullable=False)  # Cash, Card, EFT
    payment_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    
    agreement = db.relationship('RentalAgreement', backref='payments')