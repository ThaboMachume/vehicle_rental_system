from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.utils import log_action
from flask_login import current_user
from functools import wraps

admin = Blueprint('admin', __name__)

# Decorator to restrict access to Administrators only
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'Administrator':
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('bookings.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# -------- USER MANAGEMENT --------
@admin.route('/users')
@admin_required
def users():
    all_users = User.query.order_by(User.user_id).all()
    return render_template('admin/users.html', users=all_users)

@admin.route('/add-user', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        employee_id = request.form.get('employee_id')
        role = request.form.get('role')
        
        # Validation
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('admin.add_user'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return redirect(url_for('admin.add_user'))
        
        if User.query.filter_by(employee_id=employee_id).first():
            flash('Employee ID already exists.', 'danger')
            return redirect(url_for('admin.add_user'))
        
        new_user = User(
            username=username,
            employee_id=employee_id,
            role=role,
            account_status='Active'
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        log_action("User Created", "User Management", f"New {role} user '{username}' created")
        flash(f'User {username} created successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/add_user.html')

@admin.route('/toggle-user-status/<int:user_id>')
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.username == 'admin':
        flash('Cannot deactivate the primary admin account.', 'danger')
        return redirect(url_for('admin.users'))
    
    user.account_status = 'Inactive' if user.account_status == 'Active' else 'Active'
    db.session.commit()
    
    log_action("User Status Changed", "User Management", 
               f"User '{user.username}' status set to {user.account_status}")
    flash(f'User {user.username} is now {user.account_status}.', 'success')
    return redirect(url_for('admin.users'))

# -------- AUDIT LOG VIEWER --------
@admin.route('/audit-logs')
@admin_required
def audit_logs():
    logs = AuditLog.query.order_by(AuditLog.logged_at.desc()).limit(200).all()
    return render_template('admin/audit_logs.html', logs=logs)

# -------- PHASE F-4: SYSTEM ALERTS --------
@admin.route('/alerts')
@admin_required
def system_alerts():
    from app.models.vehicle import Vehicle
    from app.models.booking import Booking
    from app.models.audit_log import AuditLog
    from datetime import datetime, timedelta
    from sqlalchemy import func
    import os
    
    alerts = []
    
    # 1. Vehicles requiring maintenance (mileage > 200,000 km)
    maintenance_vehicles = Vehicle.query.filter(Vehicle.current_mileage >= 200000).all()
    for v in maintenance_vehicles:
        alerts.append({
            'level': 'warning',
            'title': f'Maintenance Due: {v.make} {v.model}',
            'message': f'Vehicle {v.license_plate} has {v.current_mileage} km — service recommended.',
            'module': 'Vehicles',
            'icon': 'bi-tools'
        })
    
    # 2. Vehicles already marked as maintenance
    in_maintenance = Vehicle.query.filter_by(status='Maintenance').all()
    for v in in_maintenance:
        alerts.append({
            'level': 'info',
            'title': f'In Maintenance: {v.make} {v.model}',
            'message': f'Vehicle {v.license_plate} is currently under maintenance.',
            'module': 'Vehicles',
            'icon': 'bi-wrench'
        })
    
    # 3. Overdue bookings (Active bookings with end_date in the past)
    today = datetime.utcnow().date()
    overdue = Booking.query.filter(
        Booking.status == 'Active',
        Booking.end_date < today
    ).all()
    for b in overdue:
        days_late = (today - b.end_date).days
        alerts.append({
            'level': 'danger',
            'title': f'Overdue Return: {b.confirmation_no}',
            'message': f'{b.customer.full_name} is {days_late} day(s) late returning {b.vehicle.license_plate}.',
            'module': 'Bookings',
            'icon': 'bi-exclamation-triangle'
        })
    
    # 4. Low disk space (check if < 500MB free — simulated for demo)
    try:
        import shutil
        total, used, free = shutil.disk_usage("/")
        free_mb = free / (1024 * 1024)
        if free_mb < 500:
            alerts.append({
                'level': 'danger',
                'title': 'Low Disk Space',
                'message': f'Only {free_mb:.0f} MB of free disk space remaining.',
                'module': 'System',
                'icon': 'bi-hdd'
            })
    except Exception:
        pass
    
    # 5. Failed login attempts (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(hours=24)
    failed_logins = AuditLog.query.filter(
        AuditLog.action == 'Failed Login',
        AuditLog.logged_at >= yesterday
    ).count()
    if failed_logins > 0:
        alerts.append({
            'level': 'warning',
            'title': 'Failed Login Attempts',
            'message': f'{failed_logins} failed login attempt(s) in the last 24 hours.',
            'module': 'Auth',
            'icon': 'bi-shield-exclamation'
        })
    
    # 6. Pending payments (Completed agreements with no payment)
    from app.models.rental_agreement import RentalAgreement
    from app.models.payment import Payment
    completed = RentalAgreement.query.filter_by(status='Completed').all()
    for a in completed:
        has_payment = Payment.query.filter_by(agreement_id=a.agreement_id).first()
        if not has_payment:
            alerts.append({
                'level': 'warning',
                'title': f'Unpaid Invoice: {a.agreement_number}',
                'message': f'Agreement for {a.booking.customer.full_name} has no payment recorded.',
                'module': 'Payments',
                'icon': 'bi-cash-coin'
            })
    
    return render_template('admin/alerts.html', alerts=alerts)