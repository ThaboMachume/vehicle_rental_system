from app import db
from datetime import datetime

class RentalAgreement(db.Model):
    __tablename__ = 'rental_agreements'
    agreement_id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.booking_id'), nullable=False)
    agreement_number = db.Column(db.String(20), unique=True, nullable=False)
    
    # Checkout Details
    checkout_odometer = db.Column(db.Integer)
    checkout_fuel_level = db.Column(db.Float)
    checkout_datetime = db.Column(db.DateTime)
    checkout_condition = db.Column(db.String(255))  # e.g., "Good, minor scratch on rear door"
    
    # Return Details
    return_odometer = db.Column(db.Integer)
    return_fuel_level = db.Column(db.Float)
    actual_return_date = db.Column(db.Date)
    return_condition = db.Column(db.String(255))
    
    # Financial Calculations
    late_fee = db.Column(db.Float, default=0.0)
    fuel_penalty = db.Column(db.Float, default=0.0)
    extras_amount = db.Column(db.Float, default=0.0)
    
    status = db.Column(db.String(20), default='Reserved')  # Reserved, Active, Completed
    
    booking = db.relationship('Booking', backref='agreement')