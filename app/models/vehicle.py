from app import db

class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    vehicle_id = db.Column(db.Integer, primary_key=True)
    make = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    license_plate = db.Column(db.String(20), unique=True, nullable=False)
    fuel_type = db.Column(db.String(20), nullable=False)  # Petrol, Diesel, Hybrid
    seating_capacity = db.Column(db.Integer, nullable=False)
    daily_rate = db.Column(db.Float, nullable=False)
    color = db.Column(db.String(30))
    current_mileage = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='Available')  # Available, Booked, Rented, Maintenance

    @property
    def id(self):
        return self.vehicle_id