from app import db
from datetime import datetime

class Booking(db.Model):
    __tablename__ = 'bookings'
    booking_id = db.Column(db.Integer, primary_key=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.vehicle_id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    rental_days = db.Column(db.Integer, nullable=False)
    confirmation_no = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default='Reserved')  # Reserved, Cancelled, Confirmed, Active, Completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    customer = db.relationship('Customer', backref='bookings')
    vehicle = db.relationship('Vehicle', backref='bookings')

    @property
    def id(self):
        return self.booking_id