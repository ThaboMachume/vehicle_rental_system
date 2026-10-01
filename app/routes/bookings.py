from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from app import db
from app.models.vehicle import Vehicle
from app.models.customer import Customer
from app.models.booking import Booking
from app.models.rental_agreement import RentalAgreement
from app.models.payment import Payment
from app.utils import log_action
from datetime import datetime, timedelta

bookings = Blueprint('bookings', __name__)

@bookings.route('/dashboard')
def dashboard():
    total_bookings = Booking.query.count()
    active_rentals = Booking.query.filter_by(status='Active').count()
    available_vehicles = Vehicle.query.filter_by(status='Available').count()
    total_customers = Customer.query.count()
    recent_bookings = Booking.query.order_by(Booking.booking_id.desc()).limit(5).all()

    return render_template('bookings/dashboard.html', 
                           total_bookings=total_bookings,
                           active_rentals=active_rentals,
                           available_vehicles=available_vehicles,
                           total_customers=total_customers,
                           recent_bookings=recent_bookings)

@bookings.route('/search-vehicles', methods=['GET', 'POST'])
def search_vehicles():
    vehicles = []
    query = ""
    if request.method == 'POST':
        query = request.form.get('query', '')
        vehicles = Vehicle.query.filter(
            (Vehicle.make.ilike(f'%{query}%')) | 
            (Vehicle.model.ilike(f'%{query}%')) |
            (Vehicle.license_plate.ilike(f'%{query}%'))
        ).all()
    else:
        vehicles = Vehicle.query.filter_by(status='Available').all()
    return render_template('bookings/search_vehicles.html', vehicles=vehicles, query=query)

@bookings.route('/add-vehicle', methods=['GET', 'POST'])
def add_vehicle():
    if request.method == 'POST':
        license_plate = request.form.get('license_plate')
        make = request.form.get('make')
        model = request.form.get('model')
        year = request.form.get('year')
        daily_rate = request.form.get('daily_rate')
        status = request.form.get('status', 'Available')
        fuel_type = request.form.get('fuel_type', 'Petrol')
        seating_capacity = request.form.get('seating_capacity', 5)
        color = request.form.get('color', 'White')
        current_mileage = request.form.get('current_mileage', 0)

        if Vehicle.query.filter_by(license_plate=license_plate).first():
            flash(f'Error: Vehicle with license plate {license_plate} already exists!', 'danger')
            return redirect(url_for('bookings.add_vehicle'))

        new_vehicle = Vehicle(
            license_plate=license_plate, make=make, model=model, year=int(year),
            daily_rate=float(daily_rate), status=status, fuel_type=fuel_type,
            seating_capacity=int(seating_capacity), color=color, current_mileage=int(current_mileage)
        )
        db.session.add(new_vehicle)
        db.session.commit()
        log_action("Vehicle Added", "Vehicles", f"Vehicle {make} {model} added")
        flash(f'Vehicle {make} {model} added successfully!', 'success')
        return redirect(url_for('bookings.search_vehicles'))
    return render_template('bookings/add_vehicle.html')

@bookings.route('/add-customer', methods=['GET', 'POST'])
def add_customer():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        id_number = request.form.get('id_number')
        drivers_license = request.form.get('drivers_license')
        address = request.form.get('address')

        if Customer.query.filter_by(email=email).first():
            flash('Email already registered.', 'danger')
            return redirect(url_for('bookings.add_customer'))
        if Customer.query.filter_by(id_number=id_number).first():
            flash('ID number already registered.', 'danger')
            return redirect(url_for('bookings.add_customer'))

        new_customer = Customer(
            full_name=full_name, email=email, phone=phone,
            id_number=id_number, drivers_license=drivers_license, address=address
        )
        db.session.add(new_customer)
        db.session.commit()
        log_action("Customer Registered", "Customers", f"Customer {full_name} registered")
        flash(f'Customer {full_name} added successfully!', 'success')
        return redirect(url_for('bookings.dashboard'))
    return render_template('bookings/add_customer.html')

@bookings.route('/book-vehicle/<int:vehicle_id>', methods=['GET', 'POST'])
def book_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    customers = Customer.query.all()
    if request.method == 'POST':
        customer_id = request.form.get('customer_id')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        if not customer_id or not start_date_str or not end_date_str:
            flash('Please fill in all fields.', 'danger')
            return redirect(url_for('bookings.book_vehicle', vehicle_id=vehicle_id))
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        days = (end_date - start_date).days
        if days <= 0:
            flash('End date must be after start date.', 'danger')
            return redirect(url_for('bookings.book_vehicle', vehicle_id=vehicle_id))
        conflict = Booking.query.filter(
            Booking.vehicle_id == vehicle_id,
            Booking.status.in_(['Reserved', 'Active']),
            Booking.end_date >= start_date, Booking.start_date <= end_date
        ).first()
        if conflict:
            flash('Conflicts with existing booking.', 'danger')
            return redirect(url_for('bookings.book_vehicle', vehicle_id=vehicle_id))
        confirmation_no = 'BK-' + datetime.now().strftime('%Y%m%d%H%M%S')
        new_booking = Booking(
            confirmation_no=confirmation_no, customer_id=int(customer_id),
            vehicle_id=vehicle_id, start_date=start_date, end_date=end_date,
            rental_days=days, status='Reserved'
        )
        db.session.add(new_booking)
        vehicle.status = 'Booked'
        db.session.commit()
        log_action("Booking Created", "Bookings", f"Booking {confirmation_no} created")
        flash(f'Booking created successfully!', 'success')
        return redirect(url_for('bookings.view_booking', booking_id=new_booking.booking_id))
    return render_template('bookings/book_vehicle.html', vehicle=vehicle, customers=customers)

# -------- FIXED: Now passes agreement to the template --------
@bookings.route('/view-booking/<int:booking_id>')
def view_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    agreement = RentalAgreement.query.filter_by(booking_id=booking_id).first()
    return render_template('bookings/view_booking.html', booking=booking, agreement=agreement)

@bookings.route('/update-booking-status/<int:booking_id>/<string:status>')
def update_booking_status(booking_id, status):
    booking = Booking.query.get_or_404(booking_id)
    booking.status = status
    if status == 'Completed':
        vehicle = Vehicle.query.get(booking.vehicle_id)
        if vehicle: vehicle.status = 'Available'
    log_action(f"Booking {status}", "Bookings", f"Booking {booking.confirmation_no} -> {status}")
    db.session.commit()
    flash(f'Booking status updated to {status}.', 'success')
    return redirect(url_for('bookings.view_booking', booking_id=booking_id))

# -------- PHASE C-1: VEHICLE CHECKOUT --------
@bookings.route('/checkout/<int:booking_id>', methods=['GET', 'POST'])
def checkout(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.status == 'Active':
        flash('This booking has already been checked out.', 'warning')
        return redirect(url_for('bookings.view_booking', booking_id=booking_id))
    if request.method == 'POST':
        checkout_odometer = request.form.get('checkout_odometer')
        checkout_fuel_level = request.form.get('checkout_fuel_level')
        checkout_condition = request.form.get('checkout_condition')
        agreement_number = 'RA-' + datetime.now().strftime('%Y%m%d%H%M%S')
        new_agreement = RentalAgreement(
            booking_id=booking_id, agreement_number=agreement_number,
            checkout_odometer=int(checkout_odometer),
            checkout_fuel_level=float(checkout_fuel_level),
            checkout_datetime=datetime.utcnow(),
            checkout_condition=checkout_condition, status='Active'
        )
        db.session.add(new_agreement)
        booking.status = 'Active'
        booking.vehicle.status = 'Rented'
        db.session.commit()
        log_action("Vehicle Checked Out", "Rental Agreements", f"Agreement {agreement_number} created")
        flash(f'Vehicle checked out successfully! Agreement: {agreement_number}', 'success')
        return redirect(url_for('bookings.view_booking', booking_id=booking_id))
    return render_template('bookings/checkout.html', booking=booking)

# -------- PHASE C-2: VEHICLE RETURN --------
@bookings.route('/return/<int:booking_id>', methods=['GET', 'POST'])
def return_vehicle(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    agreement = RentalAgreement.query.filter_by(booking_id=booking_id).first()
    
    if not agreement:
        flash('No rental agreement found for this booking.', 'warning')
        return redirect(url_for('bookings.view_booking', booking_id=booking_id))
    
    if request.method == 'POST':
        return_odometer = int(request.form.get('return_odometer'))
        return_fuel_level = float(request.form.get('return_fuel_level'))
        actual_return_date = datetime.strptime(request.form.get('actual_return_date'), '%Y-%m-%d').date()
        return_condition = request.form.get('return_condition')
        
        overdue_days = (actual_return_date - booking.end_date).days
        late_fee = 0.0
        if overdue_days > 0:
            late_fee = booking.vehicle.daily_rate * 0.15 * overdue_days
        
        fuel_penalty = 0.0
        if return_fuel_level < 90:
            fuel_deficit = 90 - return_fuel_level
            fuel_penalty = booking.vehicle.daily_rate * (fuel_deficit / 100)
        
        agreement.return_odometer = return_odometer
        agreement.return_fuel_level = return_fuel_level
        agreement.actual_return_date = actual_return_date
        agreement.return_condition = return_condition
        agreement.late_fee = late_fee
        agreement.fuel_penalty = fuel_penalty
        agreement.status = 'Completed'
        
        booking.status = 'Completed'
        booking.vehicle.current_mileage = return_odometer
        booking.vehicle.status = 'Available'
        
        db.session.commit()
        
        log_action("Vehicle Returned", "Rental Agreements", 
                   f"Agreement {agreement.agreement_number} completed. Late fee: {late_fee}, Fuel penalty: {fuel_penalty}")
        
        flash(f'Vehicle returned! Late Fee: ${late_fee:.2f}, Fuel Penalty: ${fuel_penalty:.2f}', 'success')
        return redirect(url_for('bookings.view_booking', booking_id=booking_id))
    
    return render_template('bookings/return_vehicle.html', booking=booking, agreement=agreement)

# -------- PHASE D-1: PAYMENT PROCESSING --------
@bookings.route('/payment/<int:booking_id>', methods=['GET', 'POST'])
def payment(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    agreement = RentalAgreement.query.filter_by(booking_id=booking_id).first()
    
    if not agreement:
        flash('No rental agreement found. Please complete checkout first.', 'warning')
        return redirect(url_for('bookings.view_booking', booking_id=booking_id))
    
    base_amount = booking.rental_days * booking.vehicle.daily_rate
    late_fee = agreement.late_fee or 0.0
    fuel_penalty = agreement.fuel_penalty or 0.0
    subtotal = base_amount + late_fee + fuel_penalty
    vat = subtotal * 0.15
    total_due = subtotal + vat
    
    if request.method == 'POST':
        deposit_amount = float(request.form.get('deposit_amount', 0))
        payment_method = request.form.get('payment_method', 'Cash')
        # FIXED: Prevent negative values
        total_paid = max(0, total_due - deposit_amount)
        
        transaction_id = 'TXN-' + datetime.now().strftime('%Y%m%d%H%M%S')
        
        new_payment = Payment(
            agreement_id=agreement.agreement_id,
            transaction_id=transaction_id,
            base_amount=base_amount,
            deposit_amount=deposit_amount,
            late_fee=late_fee,
            fuel_penalty=fuel_penalty,
            vat_amount=vat,
            total_paid=total_paid,
            payment_method=payment_method
        )
        
        db.session.add(new_payment)
        db.session.commit()
        
        log_action("Payment Processed", "Payments", f"Transaction {transaction_id} - ${total_paid:.2f} via {payment_method}")
        
        flash(f'Payment successful! Transaction ID: {transaction_id}', 'success')
        return redirect(url_for('bookings.view_booking', booking_id=booking_id))
    
    return render_template('bookings/payment.html', 
                           booking=booking, 
                           agreement=agreement,
                           base_amount=base_amount,
                           late_fee=late_fee,
                           fuel_penalty=fuel_penalty,
                           subtotal=subtotal,
                           vat=vat,
                           total_due=total_due)

# -------- PHASE D-2: INVOICE GENERATION --------
@bookings.route('/invoice/<int:booking_id>')
def invoice(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    agreement = RentalAgreement.query.filter_by(booking_id=booking_id).first()
    
    if not agreement:
        flash('No rental agreement found.', 'warning')
        return redirect(url_for('bookings.view_booking', booking_id=booking_id))
    
    payment = Payment.query.filter_by(agreement_id=agreement.agreement_id).first()
    
    base_amount = booking.rental_days * booking.vehicle.daily_rate
    late_fee = agreement.late_fee or 0.0
    fuel_penalty = agreement.fuel_penalty or 0.0
    subtotal = base_amount + late_fee + fuel_penalty
    vat = subtotal * 0.15
    total_due = subtotal + vat
    
    return render_template('bookings/invoice.html',
                           booking=booking,
                           agreement=agreement,
                           payment=payment,
                           base_amount=base_amount,
                           late_fee=late_fee,
                           fuel_penalty=fuel_penalty,
                           subtotal=subtotal,
                           vat=vat,
                           total_due=total_due)

# -------- PHASE F-1: CUSTOMER MANAGEMENT LIST --------
@bookings.route('/customers')
def customers():
    all_customers = Customer.query.order_by(Customer.full_name).all()
    return render_template('bookings/customers.html', customers=all_customers)

@bookings.route('/customer/<int:customer_id>')
def customer_profile(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    customer_bookings = Booking.query.filter_by(customer_id=customer_id).order_by(Booking.booking_id.desc()).all()
    return render_template('bookings/customer_profile.html', customer=customer, bookings=customer_bookings)

# -------- PHASE F-1: VEHICLE MANAGEMENT LIST --------
@bookings.route('/vehicles')
def vehicles():
    all_vehicles = Vehicle.query.order_by(Vehicle.make, Vehicle.model).all()
    return render_template('bookings/vehicles.html', vehicles=all_vehicles)

@bookings.route('/vehicle/<int:vehicle_id>')
def vehicle_profile(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    vehicle_bookings = Booking.query.filter_by(vehicle_id=vehicle_id).order_by(Booking.booking_id.desc()).all()
    return render_template('bookings/vehicle_profile.html', vehicle=vehicle, bookings=vehicle_bookings)

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
    all_agreements = RentalAgreement.query.filter_by(status='Completed').order_by(RentalAgreement.agreement_id.desc()).all()
    return render_template('bookings/all_invoices.html', agreements=all_agreements)

# -------- PHASE F-3: RENTAL AGREEMENT / CONTRACT --------
@bookings.route('/contract/<int:booking_id>')
def contract(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    agreement = RentalAgreement.query.filter_by(booking_id=booking_id).first()
    
    if not agreement:
        flash('No rental agreement found. Please complete checkout first.', 'warning')
        return redirect(url_for('bookings.view_booking', booking_id=booking_id))
    
    base_amount = booking.rental_days * booking.vehicle.daily_rate
    late_fee = agreement.late_fee or 0.0
    fuel_penalty = agreement.fuel_penalty or 0.0
    subtotal = base_amount + late_fee + fuel_penalty
    vat = subtotal * 0.15
    total_due = subtotal + vat
    
    return render_template('bookings/contract.html',
                           booking=booking,
                           agreement=agreement,
                           base_amount=base_amount,
                           late_fee=late_fee,
                           fuel_penalty=fuel_penalty,
                           subtotal=subtotal,
                           vat=vat,
                           total_due=total_due)