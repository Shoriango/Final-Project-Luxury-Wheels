from flask import Blueprint, render_template, request, session, jsonify, redirect, url_for, flash
from datetime import datetime
from . import Vehicle, Renting, db
from flask_login import current_user
from calendar import monthrange
import threading

vehicle_information = Blueprint('vehicle_information', __name__)

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

now = datetime.now()
current_year = now.year
years = {year: year for year in range(current_year, current_year + 3)}

current_month = now.month
date_changed = threading.Event()

rented_periods = []

rental_start_date = datetime(1, 1, 1)
rental_end_date = datetime(1, 1, 1)

vehicle_value = 0
total_value = 0


def get_months(selected_year):
    """
    Returns the months of the selected year
    :param selected_year:
    """
    curr_year = now.year
    updated_months = {}
    if int(selected_year) == curr_year:
        curr_month = now.month
    else:
        curr_month = 1
    for key, value in months.items():
        if key >= curr_month:
            updated_months[key] = value
    return updated_months


@vehicle_information.route('/vehicle_page/<vehicle_id>', methods=['GET', 'POST'])
def vehicle_page(vehicle_id):
    """
    Vehicle page. Only accessible if user is logged in.
    Shows the details of the vehicle and a calendar to select dates.
    Shows already rented periods.
    :param vehicle_id:
    """

    # Check if user is logged in and if vehicle exists
    global rented_periods, vehicle_value
    vehicle = Vehicle.query.get(vehicle_id)

    if not vehicle:
        flash("Vehicle not found", "error")
        return redirect(url_for('vehicle_list.vehicles'))
    car_rentals = Renting.query.filter_by(vehicle_id=vehicle_id).all()
    rented_periods = []
    vehicle_value = vehicle.daily_value
    for rents in car_rentals:
        start = rents.start_date
        end = rents.end_date
        if rents.is_active:
            rented_periods.append(
                (datetime(start.year, start.month, start.day), datetime(end.year, end.month, end.day)))
    today = datetime.today()

    current_month_days = monthrange(current_year, int(current_month))[1]
    rented_periods_str = [(start.isoformat(), end.isoformat()) for start, end in rented_periods]

    return render_template("vehicle_page.html", user=current_user,
                           vehicle=vehicle, months=get_months(current_year),
                           years=years, current_month=current_month,
                           current_year=current_year, days_month=current_month_days,
                           today=today, rented_periods=rented_periods_str,
                           rental_start_date=rental_start_date, rental_end_date=rental_end_date,
                           total_value=total_value)


@vehicle_information.route('/change-date', methods=['POST'])
def change_date():
    """
    Changes the date of the calendar
    """
    new_month = int(request.form['selected_month'])
    new_year = int(request.form['selected_year'])
    # Update session variables to keep track of the selected month and year
    if 'current_year' not in session:
        session['current_year'] = current_year
    if 'current_month' not in session:
        session['current_month'] = current_month

    updated_months = get_months(new_year)

    if new_year == session['current_year'] and new_month < session['current_month']:
        new_month = session['current_month']

    updated_month_days = monthrange(new_year, new_month)[1]
    today = datetime.today()
    actual_month = today.month

    rented_periods_str = [(start.isoformat(), end.isoformat()) for start, end in rented_periods]
    return jsonify({
        'months': updated_months,
        'selected_month': months[new_month],
        'selected_year': new_year,
        'days_month': updated_month_days,
        'today': {
            'day': today.day
        },
        'actual_month': actual_month,
        'rented_periods': rented_periods_str
    })


@vehicle_information.route('/day-click', methods=['POST'])
def day_click():
    """
    Changes the date of the start and end date when a day is clicked.
    """

    # Check if user is logged in and if vehicle exists
    global rental_start_date, rental_end_date, total_value
    day = int(request.form['day'])
    month = int(request.form['month'])
    year = int(request.form['year'])
    inserted_date = datetime(year, month, day)
    error = ""

    # Update start and end date depending on the clicked day value
    if rental_start_date.year == 1:
        rental_start_date = datetime(year, month, day)
    elif rental_start_date > inserted_date:
        rental_start_date = datetime(year, month, day)
    elif rental_start_date == inserted_date and rental_end_date.year == 1:
        rental_end_date = datetime(year, month, day)
    elif rental_start_date == inserted_date and rental_end_date == rental_start_date:
        rental_start_date = datetime(1, 1, 1)
        rental_end_date = datetime(1, 1, 1)
    elif rental_end_date > rental_start_date == inserted_date:
        rental_end_date = datetime(year, month, day)
    elif rental_start_date == inserted_date:
        rental_start_date = datetime(1, 1, 1)
    elif rental_end_date == inserted_date:
        rental_end_date = datetime(1, 1, 1)
    else:
        rental_end_date = datetime(year, month, day)

    for rentals in rented_periods:
        if rental_start_date < rentals[0] < rental_end_date and 1 not in [rental_start_date.year, rental_end_date.year]:
            rental_start_date = rental_end_date
            rental_end_date = datetime(1, 1, 1)

    if rental_start_date.year == 1 or rental_end_date.year == 1:
        total_value = -1
    else:
        days = (rental_end_date - rental_start_date).days + 1
        total_value = float(days * vehicle_value)
        total_value = f"{total_value:.2f}"

    return jsonify({
        'start_date_day': rental_start_date.day,
        'start_date_month': months[rental_start_date.month],
        'start_date_year': rental_start_date.year,
        'end_date_day': rental_end_date.day,
        'end_date_month': months[rental_end_date.month],
        'end_date_year': rental_end_date.year,
        'total_value': total_value,
        'error': error
    })


@vehicle_information.route('/reset-dates', methods=['POST'])
def reset_dates():
    """
    Resets the dates of the start and end date when the reset button is clicked.
    """

    # Reset start and end date when reset button is clicked
    global rental_start_date, rental_end_date, total_value
    rental_start_date = datetime(1, 1, 1)
    rental_end_date = datetime(1, 1, 1)
    total_value = -1
    return jsonify({
        'success': True
    })


@vehicle_information.route('/submit-rental-dates', methods=['POST'])
def redirect_rental():
    """
    Redirects to the rent vehicle page when the submit button is clicked.

    """
    global rental_start_date, rental_end_date, total_value
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    # Check if user is logged in and if vehicle exists
    redir_start_date = rental_start_date
    redir_end_date = rental_end_date
    redir_value = total_value

    vehicle_id = request.form.get('vehicle_id')

    # Redirect to rent vehicle page when submit button is clicked
    if rental_start_date.year == 1 or rental_end_date.year == 1:
        flash('Start date and end date must be filled', category='error')
        return redirect(url_for('vehicle_information.vehicle_page', vehicle_id=vehicle_id))
    else:
        rental_start_date = datetime(1, 1, 1)
        rental_end_date = datetime(1, 1, 1)
        total_value = -1
        return redirect(
            url_for('renting_page.rent_vehicle', start_date=redir_start_date, end_date=redir_end_date,
                    vehicle_id=vehicle_id, total_value=redir_value))


@vehicle_information.route('/remove-vehicle/<int:vehicle_id>', methods=['POST'])
def remove_vehicle(vehicle_id):
    """
    Removes a vehicle from the database. Only accessible to admins.
    :param vehicle_id:
    """

    # Check if user is logged in and if user is admin
    if not current_user.is_authenticated or current_user.user_type != 'admin':
        flash("You do not have permission to perform this action.", "error")
        return redirect(url_for('vehicle_list.vehicles'))

    vehicle = Vehicle.query.get(vehicle_id)

    if not vehicle:
        flash("Vehicle not found", "error")
        return redirect(url_for('vehicle_list.vehicles'))
    try:
        # Delete the vehicle
        db.session.delete(vehicle)
        db.session.commit()
        flash("Vehicle removed successfully", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred while trying to remove the vehicle: {e}", "error")

    return redirect(url_for('vehicle_list.vehicles'))
