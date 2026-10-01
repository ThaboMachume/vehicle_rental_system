from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User
from app.utils import log_action
from datetime import datetime

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # If already logged in, route them based on their role
        if current_user.role == 'Manager':
            return redirect(url_for('reports.dashboard'))
        return redirect(url_for('bookings.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.account_status == 'Active':
            # Set up the session timestamp for auto-logout
            login_user(user)
            session.permanent = True
            session['last_activity'] = datetime.utcnow().isoformat()
            
            # Update the last login time
            user.last_login = datetime.utcnow()
            db.session.commit()
            log_action("User Login", "Auth", f"{user.username} logged in")
            
            # ROLE-BASED ROUTING
            if user.role == 'Manager':
                return redirect(url_for('reports.dashboard'))
            else:
                return redirect(url_for('bookings.dashboard'))
        else:
            flash('Invalid username or password, or account is inactive.', 'danger')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    log_action("User Logout", "Auth", f"{current_user.username} logged out")
    logout_user()
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

# -------- FORGOT PASSWORD FLOW --------
@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username')
        employee_id = request.form.get('employee_id')
        
        user = User.query.filter_by(username=username, employee_id=employee_id).first()
        
        if user:
            # Store a temporary reset marker in the session
            reset_token = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            session['reset_user_id'] = user.user_id
            session['reset_token'] = reset_token
            log_action("Password Reset Requested", "Auth", f"User {username} requested password reset")
            flash('Identity verified. Please set a new password.', 'success')
            return redirect(url_for('auth_bp.reset_password'))
        else:
            flash('No account found with that username and employee ID.', 'danger')
    
    return render_template('auth/forgot_password.html')

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    # Ensure the user has been verified
    user_id = session.get('reset_user_id')
    if not user_id:
        flash('Please verify your identity first.', 'warning')
        return redirect(url_for('auth_bp.forgot_password'))
    
    user = User.query.get(user_id)
    if not user:
        session.pop('reset_user_id', None)
        session.pop('reset_token', None)
        flash('Invalid reset session.', 'danger')
        return redirect(url_for('auth_bp.forgot_password'))
    
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not new_password or len(new_password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return redirect(url_for('auth_bp.reset_password'))
        
        if new_password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('auth_bp.reset_password'))
        
        # Update the password
        user.set_password(new_password)
        db.session.commit()
        
        log_action("Password Reset Completed", "Auth", f"User {user.username} reset their password")
        
        # Clear reset session
        session.pop('reset_user_id', None)
        session.pop('reset_token', None)
        
        flash('Your password has been reset successfully! Please log in.', 'success')
        return redirect(url_for('auth_bp.login'))
    
    return render_template('auth/reset_password.html', user=user)