from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from . import Payment, db
import hashlib

profile_page = Blueprint('profile_page', __name__)


def hash_card_number(card_number):
    """
    Hashes the card number using SHA-256
    :param card_number:
    :return: card number hashed
    """
    return hashlib.sha256(card_number.encode()).hexdigest()


@profile_page.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    Profile page. Only accessible if user is logged in.
    Displays profile information and payment methods.
    Allows user to update profile and change password and add payment methods.
    """
    if request.method == 'POST':
        if 'update_profile' in request.form:
            # Handle profile update
            current_user.first_name = request.form.get('first_name')
            current_user.phone_number = request.form.get('phone_number')
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        elif 'change_password' in request.form:
            # Handle password change
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            if not check_password_hash(current_user.password, current_password):
                flash('Current password is incorrect.', 'error')
            elif new_password != confirm_password:
                flash('New passwords do not match.', 'error')
            else:
                current_user.password = generate_password_hash(new_password, method='scrypt')
                db.session.commit()
                flash('Password updated successfully!', 'success')
        return redirect(url_for('profile_page.profile'))

    # Fetch payment methods for the current user
    payment_methods = Payment.query.filter_by(user_id=current_user.id).all()

    return render_template('profile.html', user=current_user, payment_methods=payment_methods)


@profile_page.route('/profile/add_payment_method', methods=['POST'])
@login_required
def add_payment_method():
    """
    Adds a new payment method for the current user
    :param request:
    """
    payment_method = request.form.get('newPaymentMethod')

    if payment_method == 'Credit Card':
        card_number = request.form.get('cardNumber')
        if not card_number.isdigit() or len(card_number) != 16:
            flash('Credit card number not valid', 'error')
            return redirect(url_for('profile_page.profile'))

        card_last_four = card_number[-4:]
        card_hash = hash_card_number(card_number)

        # Check if the card already exists for the user by comparing hashes
        existing_card = Payment.query.filter_by(user_id=current_user.id, card_hash=card_hash).first()
        if existing_card:
            flash('Credit card already added!', 'error')
            return redirect(url_for('profile_page.profile'))

        payment = Payment(
            method=payment_method,
            amount=0,
            status='Active',
            user_id=current_user.id,
            card_last_four=card_last_four,
            card_hash=card_hash  # Store the hash of the card number
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
        # Check if the PayPal email already exists for the user
        existing_paypal = Payment.query.filter_by(user_id=current_user.id, email=paypal_email).first()
        if existing_paypal:
            flash('PayPal email already added!', 'error')
            return redirect(url_for('profile_page.profile'))

        payment = Payment(
            method=payment_method,
            amount=0,
            status='Active',
            user_id=current_user.id,
            email=paypal_email
        )

    db.session.add(payment)
    db.session.commit()

    flash('Payment method added successfully!', 'success')
    return redirect(url_for('profile_page.profile'))


@profile_page.route('/profile/delete_payment_method/<int:payment_id>', methods=['POST'])
@login_required
def delete_payment_method(payment_id):
    """
    Deletes a payment method for the current user
    :param payment_id:
    :return:
    """
    payment = Payment.query.get_or_404(payment_id)
    if payment.user_id != current_user.id:
        flash('You do not have permission to delete this payment method.', 'error')
        return redirect(url_for('profile_page.profile'))

    db.session.delete(payment)
    db.session.commit()
    flash('Payment method deleted successfully!', 'success')
    return redirect(url_for('profile_page.profile'))
