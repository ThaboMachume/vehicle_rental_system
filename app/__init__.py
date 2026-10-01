import pymysql
pymysql.install_as_MySQLdb()

from flask import Flask, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, logout_user
from flask_migrate import Migrate
from config import Config
from datetime import datetime, timedelta

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    from app.models.user import User
    return User.query.get(int(user_id))

def create_app():
    app = Flask(__name__)
    
    app.config.from_object(Config)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
    app.config['SECRET_KEY'] = 'your-secret-key'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    # -------- AUTO-LOGOUT AFTER 15 MINUTES --------
    @app.before_request
    def check_session_timeout():
        from flask import request
        # Skip static files
        if request.endpoint and 'static' in request.endpoint:
            return
        
        if current_user.is_authenticated:
            now = datetime.utcnow()
            last_activity = session.get('last_activity')
            
            if last_activity:
                try:
                    last_dt = datetime.fromisoformat(last_activity)
                except (ValueError, TypeError):
                    last_dt = None
                
                if last_dt and (now - last_dt) > timedelta(minutes=15):
                    # Session expired
                    logout_user()
                    session.clear()
                    flash('Your session has expired due to inactivity. Please log in again.', 'warning')
                    return redirect(url_for('auth.login'))
            
            # Refresh the timestamp on every request
            session['last_activity'] = now.isoformat()
            session.permanent = True

    # Register Blueprints
    from app.routes.auth import auth_bp
    app.register_blueprint(auth_bp)

    from app.routes.bookings import bookings
    app.register_blueprint(bookings)

    from app.routes.reports import reports
    app.register_blueprint(reports, url_prefix='/reports')

    from app.routes.admin import admin
    app.register_blueprint(admin)

    # Debug print
    print("\n=== BLUEPRINTS REGISTERED ===")
    for name, bp in app.blueprints.items():
        print(f"  {name}")
    print("=== END ===\n")

    return app