from flask import Blueprint, render_template, request, redirect, url_for, flash
from . import Vehicle, db
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from PIL import Image

add_vehicle_page = Blueprint('add_vehicle_page', __name__)

UPLOAD_FOLDER = r'website\static\car_images'
ALLOWED_EXTENSIONS = {'png', 'jpeg', 'jpg'}


def allowed_file(filename):
    """
    Check if file extension is allowed
    :param filename:
    :return:
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def resize_image(image_path, max_width, max_height):
    """
    Resize the image to the specified dimensions.
    :param image_path:
    :param max_width:
    :param max_height:
    :return:
    """
    with Image.open(image_path) as img:
        img.thumbnail((max_width, max_height))
        img.save(image_path)


def cleanup_unused_images():
    """
    Cleanup images not used in the database.
    """
    vehicle_images = Vehicle.query.with_entities(Vehicle.image_path).all()
    all_images = []
    for image in vehicle_images:
        image = str(image[0])
        last_slash = image.rfind('\\')
        all_images.append(image[last_slash + 1:])
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename not in all_images:
            os.remove(os.path.join(UPLOAD_FOLDER, filename))


@add_vehicle_page.route('/add_vehicle', methods=['GET', 'POST'])
@login_required
def add_vehicle():
    """
    Add a new vehicle to the database and redirect to the vehicle list.
    Only admins can access this page.
    """
    if request.method == 'GET':
        cleanup_unused_images()
        return render_template('add_vehicle.html', user=current_user)
    if current_user.user_type != 'admin':
        return redirect(url_for('vehicle_list.vehicles'))

    if request.method == 'POST':
        try:
            brand = request.form['brand']
            model = request.form['model']
            category = request.form['category']
            year = int(request.form['year'])
            vehicle_type = request.form['vehicle_type']
            capacity = int(request.form['capacity'])
            transmission = request.form['transmission']
            daily_value = float(request.form['daily_value'])
            last_maintenance = datetime.strptime(request.form['last_maintenance'], '%Y-%m-%d')
            next_maintenance = datetime.strptime(request.form['next_maintenance'], '%Y-%m-%d')
            last_legalisation = datetime.strptime(request.form['last_legalisation'], '%Y-%m-%d')
            mileage = int(request.form['mileage'])
            registration_expiry_date = datetime.strptime(request.form['registration_expiry_date'], '%Y-%m-%d')
            vin = request.form['vin']
            license_plate = request.form['license_plate']
            fuel_type = request.form['fuel_type']
            color = request.form['color']
            condition = request.form['condition']
            num_doors = int(request.form['num_doors'])
            horsepower = int(request.form['horsepower'])
            image_file = request.files['image_file']

            if not (1980 <= year <= datetime.now().year):
                flash('Year must be between 1980 and current year.', 'error')
                return redirect(url_for('add_vehicle_page.add_vehicle'))

            if not (1 <= capacity <= 20):
                flash('Capacity must be between 1 and 20.', 'error')
                return redirect(url_for('add_vehicle_page.add_vehicle'))

            if not (0 <= horsepower <= 1000):
                flash('Horsepower must be between 0 and 1000.', 'error')
                return redirect(url_for('add_vehicle_page.add_vehicle'))

            if not (1 <= daily_value <= 2000):
                flash('Daily rental price must be between 1 and 2000.', 'error')
                return redirect(url_for('add_vehicle_page.add_vehicle'))

            if not (1 <= mileage <= 1000000):
                flash('Mileage must be between 1 and 1,000,000.', 'error')
                return redirect(url_for('add_vehicle_page.add_vehicle'))

            if not (0 <= num_doors <= 7):
                flash('Number of doors must be between 0 and 7.', 'error')
                return redirect(url_for('add_vehicle_page.add_vehicle'))

            for vehicle in Vehicle.query.all():
                if vehicle.vin == vin:
                    flash('VIN already exists.', 'error')
                    return redirect(url_for('add_vehicle_page.add_vehicle'))

                if vehicle.license_plate == license_plate:
                    flash('License plate already exists.', 'error')
                    return redirect(url_for('add_vehicle_page.add_vehicle'))

            if image_file and allowed_file(image_file.filename):
                filename = secure_filename(f"{model}_{brand}")
                filename = filename + "_" + str(uuid.uuid4()) + ".png"
                image_path = os.path.join(UPLOAD_FOLDER, filename)
                image_file.save(os.path.join(os.getcwd(), image_path))

                # Resize image
                resize_image(image_path, 667, 374)
            else:
                flash('Please upload a png, jpg, or jpeg file.', 'error')
                return redirect(url_for('add_vehicle_page.add_vehicle'))

            new_vehicle = Vehicle(
                brand=brand,
                model=model,
                category=category,
                year=year,
                vehicle_type=vehicle_type,
                capacity=capacity,
                transmission=transmission,
                daily_value=daily_value,
                last_maintenance=last_maintenance,
                next_maintenance=next_maintenance,
                last_legalisation=last_legalisation,
                mileage=mileage,
                registration_expiry_date=registration_expiry_date,
                vin=vin,
                license_plate=license_plate,
                fuel_type=fuel_type,
                color=color,
                condition=condition,
                num_doors=num_doors,
                horsepower=horsepower,
                image_path=rf"\static\car_images\{filename}"
            )

            db.session.add(new_vehicle)
            db.session.commit()

            # Cleanup unused images after successfully adding a new vehicle
            cleanup_unused_images()

            flash('Vehicle added successfully.', 'success')
            return redirect(url_for('vehicle_list.vehicles'))

        except ValueError:
            flash('Invalid input for numeric fields.', 'error')
            return redirect(url_for('add_vehicle_page.add_vehicle'))

    return render_template('add_vehicle.html', user=current_user, current_year=datetime.now().year)
