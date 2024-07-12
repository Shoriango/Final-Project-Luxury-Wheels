from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from . import Renting, Vehicle, Payment, db
from datetime import datetime
import hashlib

renting_page = Blueprint('renting_page', __name__)

total_value = 0


def hash_card_number(card_number):
    """
    Hashes the card number using SHA-256
    :param card_number:
    :return: card number hashed
    """
    return hashlib.sha256(card_number.encode()).hexdigest()


@renting_page.route('/rent_vehicle', methods=['GET', 'POST'])
@login_required
def rent_vehicle():
    """
    Renting page. Only accessible if user is logged in.
    Allows user to rent a vehicle.
    """
    global total_value
    months = {
        1: "January",
        2: "February",
        3: "March",
        4: "April",
        5: "May",
        6: "June",
        7: "July",
        8: "August",
        9: "September",
        10: "October",
        11: "November",
        12: "December",
    }

    if request.method == 'GET':
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        vehicle_id = request.args.get('vehicle_id')
        total_value = request.args.get('total_value')
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")
    else:
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        vehicle_id = request.form.get('vehicle_id')
        total_value = request.form.get('total_value')

        start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")

    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        flash("Vehicle not found", "error")
        return redirect(url_for('vehicle_list.vehicles', vehicle_id=vehicle_id))
    car_rentals = Renting.query.filter_by(vehicle_id=vehicle_id).all()
    rented_periods = []
    for rents in car_rentals:
        start = rents.start_date
        end = rents.end_date
        if rents.is_active:
            rented_periods.append(
                (datetime(start.year, start.month, start.day), datetime(end.year, end.month, end.day)))
        for period in rented_periods:
            if period[0] <= start_date <= period[1]:
                flash("Vehicle is not available", "error")
                return redirect(url_for('vehicle_list.vehicles'))
            elif period[0] <= end_date <= period[1]:
                flash("Vehicle is not available", "error")
                return redirect(url_for('vehicle_list.vehicles'))
    payment_methods = Payment.query.filter_by(user_id=current_user.id).all()

    return render_template("rent_vehicle.html", user=current_user, start_date=start_date, end_date=end_date,
                           vehicle=vehicle, total_value=total_value, months=months, payment_methods=payment_methods)


@renting_page.route('/add_payment_method', methods=['POST'])
@login_required
def add_payment_method():
    """
    Adds a new payment method for the current user
    """
    payment_method = request.form.get('newPaymentMethod')

    if payment_method == 'Credit Card':
        card_number = request.form.get('cardNumber')
        if not card_number.isdigit() or len(card_number) != 16:
            flash('Credit card number not valid', 'error')
            return redirect(url_for('renting_page.rent_vehicle', start_date=request.form.get('start_date'),
                                    end_date=request.form.get('end_date'), vehicle_id=request.form.get('vehicle_id'),
                                    total_value=request.form.get('total_value')))

        card_last_four = card_number[-4:]
        card_hash = hash_card_number(card_number)

        # Check if the card already exists for the user by comparing hashes
        existing_card = Payment.query.filter_by(user_id=current_user.id, card_hash=card_hash).first()
        if existing_card:
            flash('Credit card already exists!', 'error')
            return redirect(url_for('renting_page.rent_vehicle', start_date=request.form.get('start_date'),
                                    end_date=request.form.get('end_date'), vehicle_id=request.form.get('vehicle_id'),
                                    total_value=request.form.get('total_value')))

        payment = Payment(
            method=payment_method,
            status='Active',
            user_id=current_user.id,
            card_last_four=card_last_four,
            card_hash=card_hash
        )

    elif payment_method == 'PayPal':
        paypal_email = request.form.get('paypalEmail')
        if paypal_email == '':
            flash('PayPal email cannot be empty!', 'error')
            return redirect(url_for('renting_page.rent_vehicle', start_date=request.form.get('start_date'),
                                    end_date=request.form.get('end_date'), vehicle_id=request.form.get('vehicle_id'),
                                    total_value=request.form.get('total_value')))
        if '@' not in paypal_email:
            flash('PayPal email is not valid!', 'error')
            return redirect(url_for('renting_page.rent_vehicle', start_date=request.form.get('start_date'),
                                    end_date=request.form.get('end_date'), vehicle_id=request.form.get('vehicle_id'),
                                    total_value=request.form.get('total_value')))
        existing_paypal = Payment.query.filter_by(user_id=current_user.id, email=paypal_email).first()
        if existing_paypal:
            flash('PayPal email already exists!', 'error')
            return redirect(url_for('renting_page.rent_vehicle', start_date=request.form.get('start_date'),
                                    end_date=request.form.get('end_date'), vehicle_id=request.form.get('vehicle_id'),
                                    total_value=request.form.get('total_value')))

        payment = Payment(
            method=payment_method,
            status='Active',
            user_id=current_user.id,
            email=paypal_email
        )

    db.session.add(payment)
    db.session.commit()

    flash('Payment method added successfully!', 'success')
    return redirect(url_for('renting_page.rent_vehicle', start_date=request.form.get('start_date'),
                            end_date=request.form.get('end_date'), vehicle_id=request.form.get('vehicle_id'),
                            total_value=request.form.get('total_value')))


@renting_page.route('/process_payment', methods=['POST'])
@login_required
def process_payment():
    """
    Processes the payment for the current user

    """
    payment_method_id = request.form.get('paymentMethod')
    start_date = datetime.strptime(request.form.get('start_date'), "%Y-%m-%d %H:%M:%S")
    end_date = datetime.strptime(request.form.get('end_date'), "%Y-%m-%d %H:%M:%S")
    vehicle_id = request.form.get('vehicle_id')
    payment = Payment.query.get(payment_method_id)
    payment.status = 'Completed'
    db.session.commit()
    renting = Renting(
        start_date=start_date,
        end_date=end_date,
        is_active=True,
        total_cost=total_value,
        user_id=current_user.id,
        vehicle_id=vehicle_id
    )

    db.session.add(renting)
    db.session.commit()

    flash('Vehicle rented successfully!', 'success')
    return redirect(url_for('vehicle_information.vehicle_page', vehicle_id=vehicle_id))
