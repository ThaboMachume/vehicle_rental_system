from app import db
from datetime import datetime

class Booking(db.Model):
    __tablename__ = 'bookings'

    booking_id = db.Column(db.Integer, primary_key=True)
    confirmation_no = db.Column(db.String(20), unique=True, nullable=False)
    
    # Foreign keys linking to Customers and Vehicles
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.customer_id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)  # FIXED THIS LINE
    
    # Dates
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Money
    total_cost = db.Column(db.Float, nullable=False)
    
    # Status
    status = db.Column(db.String(20), default='Reserved')  # 'Reserved', 'Confirmed', 'Active', 'Completed', 'Cancelled'
    
    # Relationships
    customer = db.relationship('Customer', backref='bookings')
    vehicle = db.relationship('Vehicle', backref='bookings')

    def __repr__(self):
        return f'<Booking {self.confirmation_no}>'

    # -------- PHASE F-2: BOOKING MANAGEMENT LIST --------
@bookings.route('/bookings')
def all_bookings():
    status_filter = request.args.get('status', '')
    if status_filter:
        all_bkgs = Booking.query.filter_by(status=status_filter).order_by(Booking.booking_id.desc()).all()
    else:
        all_bkgs = Booking.query.order_by(Booking.booking_id.desc()).all()
    return render_template('bookings/all_bookings.html', bookings=all_bkgs, status_filter=status_filter)

# -------- PHASE F-2: PAYMENT HISTORY --------
@bookings.route('/payments')
def all_payments():
    all_pmts = Payment.query.order_by(Payment.payment_id.desc()).all()
    return render_template('bookings/all_payments.html', payments=all_pmts)

# -------- PHASE F-2: INVOICE HISTORY --------
@bookings.route('/invoices')
def all_invoices():
    # Get all completed agreements with payments
    all_agreements = RentalAgreement.query.filter_by(status='Completed').order_by(RentalAgreement.agreement_id.desc()).all()
    return render_template('bookings/all_invoices.html', agreements=all_agreements)