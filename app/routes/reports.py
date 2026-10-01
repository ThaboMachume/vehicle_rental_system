from flask import Blueprint, render_template, request
from app.models.vehicle import Vehicle
from app.models.booking import Booking
from app.models.customer import Customer
from app.models.payment import Payment
from app import db
from sqlalchemy import func

reports = Blueprint('reports', __name__)

@reports.route('/dashboard')
def dashboard():
    total_vehicles = Vehicle.query.count()
    available_vehicles = Vehicle.query.filter_by(status='Available').count()
    booked_vehicles = Vehicle.query.filter_by(status='Booked').count()
    rented_vehicles = Vehicle.query.filter_by(status='Rented').count()
    maintenance_vehicles = Vehicle.query.filter_by(status='Maintenance').count()
    total_bookings = Booking.query.count()
    active_rentals = Booking.query.filter_by(status='Active').count()
    total_customers = Customer.query.count()
    total_revenue = db.session.query(func.sum(Payment.total_paid)).scalar() or 0
    recent_bookings = Booking.query.order_by(Booking.booking_id.desc()).limit(5).all()

    cash_revenue = db.session.query(func.sum(Payment.total_paid)).filter(Payment.payment_method == 'Cash').scalar() or 0
    card_revenue = db.session.query(func.sum(Payment.total_paid)).filter(Payment.payment_method == 'Card').scalar() or 0
    eft_revenue = db.session.query(func.sum(Payment.total_paid)).filter(Payment.payment_method == 'EFT').scalar() or 0

    monthly_revenue = db.session.query(
        func.strftime('%Y-%m', Payment.payment_datetime).label('month'),
        func.sum(Payment.total_paid).label('total')
    ).group_by('month').order_by('month').limit(6).all()
    
    monthly_labels = [row.month for row in monthly_revenue]
    monthly_totals = [float(row.total) for row in monthly_revenue]

    return render_template(
        'reports/dashboard.html',
        total_vehicles=total_vehicles,
        available_vehicles=available_vehicles,
        booked_vehicles=booked_vehicles,
        rented_vehicles=rented_vehicles,
        maintenance_vehicles=maintenance_vehicles,
        total_bookings=total_bookings,
        active_rentals=active_rentals,
        total_customers=total_customers,
        total_revenue=total_revenue,
        recent_bookings=recent_bookings,
        cash_revenue=float(cash_revenue),
        card_revenue=float(card_revenue),
        eft_revenue=float(eft_revenue),
        monthly_labels=monthly_labels,
        monthly_totals=monthly_totals
    )

# -------- PHASE F-5: DAILY SALES REPORT --------
@reports.route('/daily-sales', methods=['GET', 'POST'])
def daily_sales():
    from datetime import datetime, date
    from sqlalchemy import func
    
    selected_date = request.form.get('report_date') if request.method == 'POST' else date.today().isoformat()
    
    try:
        target_date = datetime.strptime(selected_date, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        target_date = date.today()
        selected_date = target_date.isoformat()
    
    # Get all payments for that date
    payments = Payment.query.filter(
        func.date(Payment.payment_datetime) == target_date
    ).all()
    
    total_sales = sum(p.total_paid for p in payments)
    transaction_count = len(payments)
    cash_total = sum(p.total_paid for p in payments if p.payment_method == 'Cash')
    card_total = sum(p.total_paid for p in payments if p.payment_method == 'Card')
    eft_total = sum(p.total_paid for p in payments if p.payment_method == 'EFT')
    
    return render_template('reports/daily_sales.html',
                           selected_date=selected_date,
                           payments=payments,
                           total_sales=total_sales,
                           transaction_count=transaction_count,
                           cash_total=cash_total,
                           card_total=card_total,
                           eft_total=eft_total)


# -------- PHASE F-5: CUSTOMER RENTAL HISTORY --------
@reports.route('/customer-history', methods=['GET', 'POST'])
def customer_history():
    from app.models.booking import Booking
    
    customer = None
    bookings = []
    total_rentals = 0
    total_spent = 0.0
    avg_duration = 0.0
    
    if request.method == 'POST':
        customer_id = request.form.get('customer_id', '').strip()
        customer_name = request.form.get('customer_name', '').strip()
        
        if customer_id:
            customer = Customer.query.get(customer_id)
        elif customer_name:
            customer = Customer.query.filter(Customer.full_name.ilike(f'%{customer_name}%')).first()
        
        if customer:
            bookings = Booking.query.filter_by(customer_id=customer.customer_id).order_by(Booking.booking_id.desc()).all()
            total_rentals = len(bookings)
            if total_rentals > 0:
                avg_duration = sum(b.rental_days for b in bookings) / total_rentals
            
            # Calculate total spent from payments
            from app.models.rental_agreement import RentalAgreement
            for b in bookings:
                agreement = RentalAgreement.query.filter_by(booking_id=b.booking_id).first()
                if agreement:
                    total_spent += sum(p.total_paid for p in agreement.payments) if agreement.payments else 0
    
    return render_template('reports/customer_history.html',
                           customer=customer,
                           bookings=bookings,
                           total_rentals=total_rentals,
                           total_spent=total_spent,
                           avg_duration=avg_duration)