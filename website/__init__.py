from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask_login import UserMixin
from datetime import datetime

app = Flask(__name__)

basedir = path.abspath(path.dirname(__file__))

# Configuration for the databae
app.config['SQLALCHEMY_DATABASE_URI'] = \
    'sqlite:///' + path.join(basedir, 'databases/website.db')

app.config['SECRET_KEY'] = 'ASDL0SDIMFG89KSD'

db = SQLAlchemy(app)


# Database tables for the website
class User(db.Model, UserMixin):
    """
    User database table, contains:
    ID, email, password, first_name, user_type, phone_number, creation_date

    outputs a connection to payment table and renting table
    """
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    user_type = db.Column(db.String(150))
    phone_number = db.Column(db.String(50))
    creation_date = db.Column(db.DateTime, default=datetime.utcnow())

    rentings = db.relationship('Renting')
    payments = db.relationship('Payment')


class Vehicle(db.Model):
    """
    Vehicle database table, contains:

    ID, brand, model, category, year, vehicle_type, capacity, image_path,
    transmission, daily_value, last_maintenance, next_maintenance,
    last_legalisation, mileage, registration_expiry_date, vin,
    license_plate, fuel_type, color, condition, num_doors, horsepower

    outputs a connection to renting table
    """
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(150))
    model = db.Column(db.String(150))
    category = db.Column(db.String(150))
    year = db.Column(db.String(150))
    vehicle_type = db.Column(db.String(150))
    capacity = db.Column(db.Integer)
    image_path = db.Column(db.String(120), nullable=False)
    transmission = db.Column(db.String(150))
    daily_value = db.Column(db.Numeric(precision=10, scale=2))
    last_maintenance = db.Column(db.DateTime)
    next_maintenance = db.Column(db.DateTime)
    last_legalisation = db.Column(db.DateTime)
    mileage = db.Column(db.Integer)
    registration_expiry_date = db.Column(db.DateTime)
    vin = db.Column(db.String(100), unique=True)
    license_plate = db.Column(db.String(50), unique=True)
    fuel_type = db.Column(db.String(50))
    color = db.Column(db.String(50))
    condition = db.Column(db.String(150))
    num_doors = db.Column(db.Integer)
    horsepower = db.Column(db.Integer)

    rentings = db.relationship('Renting')


class Renting(db.Model):
    """
    Renting database table, contains:

    ID, start_date, end_date, is_active, total_cost, user_id, vehicle_id

    connects to vehicle table by vehicle_id and user table by user_id
    """
    id = db.Column(db.Integer, primary_key=True)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=False)
    total_cost = db.Column(db.Numeric(precision=10, scale=2))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicle.id'))


class Payment(db.Model):
    """
    Payment database table, contains:

    ID, method, payment_date, status, card_last_four, card_hash, email,
    user_id

    connects to user table by user_id
    """
    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.String(150))
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(50))
    card_last_four = db.Column(db.String(4))
    card_hash = db.Column(db.String(64), unique=True)
    email = db.Column(db.String(150))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


with app.app_context():
    db.create_all()


def create_app():
    """
    Creates the app, registers the blueprints, and returns the app
    """
    from .main_page import root
    from .auth import auth
    from .search_vehicles import vehicle_list
    from .vehicle_info import vehicle_information
    from .rent_vehicle import renting_page
    from .profile import profile_page
    from .user_rentals import rentals_page
    from .add_vehicle import add_vehicle_page

    app.register_blueprint(root, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(vehicle_list, url_prefix='/')
    app.register_blueprint(vehicle_information, url_prefix='/')
    app.register_blueprint(renting_page, url_prefix='/renting_page')
    app.register_blueprint(profile_page, url_prefix='/')
    app.register_blueprint(rentals_page, url_prefix='/')
    app.register_blueprint(add_vehicle_page, url_prefix='/')

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app
