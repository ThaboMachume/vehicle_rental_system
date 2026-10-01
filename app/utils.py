from app import db
from app.models.audit_log import AuditLog
from flask_login import current_user
from datetime import datetime

def log_action(action, module, description=""):
    """
    Records an action in the audit log.
    Usage: log_action("Created Booking", "Bookings", f"Booking {booking_id} created")
    """
    if current_user.is_authenticated:
        log = AuditLog(
            user_id=current_user.user_id,
            action=action,
            module=module,
            description=description,
            logged_at=datetime.utcnow()
        )
        db.session.add(log)
        db.session.commit()