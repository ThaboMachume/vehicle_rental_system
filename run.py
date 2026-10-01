from app import create_app, db
from app.models.user import User
from app.models.vehicle import Vehicle
from app.models.customer import Customer
from app.models.booking import Booking
from app.models.rental_agreement import RentalAgreement
from app.models.payment import Payment
from app.models.audit_log import AuditLog

app = create_app()

with app.app_context():
    # WARNING: db.drop_all() wipes ALL data. It is now DISABLED.
    # Uncomment the line below ONLY if you need to reset the database completely.
    # db.drop_all()
    
    # Creates tables only if they don't already exist (safe to run every time)
    db.create_all()
    
    # Recreate default users (only if they don't exist)
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', role='Administrator', employee_id='EMP001')
        admin.set_password('admin123')
        db.session.add(admin)
        print("✅ Admin user created!")
    
    if not User.query.filter_by(username='manager').first():
        manager = User(username='manager', role='Manager', employee_id='EMP002')
        manager.set_password('manager123')
        db.session.add(manager)
        print("✅ Manager user created!")
    
    if not User.query.filter_by(username='clerk').first():
        clerk = User(username='clerk', role='Clerk', employee_id='EMP003')
        clerk.set_password('clerk123')
        db.session.add(clerk)
        print("✅ Clerk user created!")
    
    db.session.commit()
    print("✅ Database setup complete!")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)