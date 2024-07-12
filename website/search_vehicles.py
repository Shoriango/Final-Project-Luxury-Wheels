from flask import Blueprint, render_template, request
from . import Vehicle, Renting, db
from flask_login import current_user
from sqlalchemy import or_
from datetime import datetime, timedelta

vehicle_list = Blueprint('vehicle_list', __name__)


@vehicle_list.route('/vehicles', methods=['GET', 'POST'])
def vehicles():
    """
    Vehicle list page. Allows user to search vehicles.
    """
    search_query = request.form.get('search-input', '')
    price_range = request.form.get('price-range', 2000)
    num_doors = request.form.getlist('num-doors') or []
    vehicle_type = request.form.get('vehicle-type', '')
    transmission = request.form.get('transmission', '')
    fuel_type = request.form.get('fuel-type', '')
    condition = request.form.get('condition', '')

    search_conditions = []

    # Add search conditions based on user input values
    if search_query:
        search_conditions.append(
            or_(Vehicle.brand.ilike(f'%{search_query}%'),
                Vehicle.model.ilike(f'%{search_query}%'),
                Vehicle.year.ilike(f'%{search_query}%'),
                Vehicle.category.ilike(f'%{search_query}%'))
        )
    if price_range:
        search_conditions.append(Vehicle.daily_value <= price_range)
    if num_doors:
        search_conditions.append(Vehicle.num_doors.in_(num_doors))
    if vehicle_type:
        search_conditions.append(Vehicle.category.ilike(f'%{vehicle_type}%'))
    if transmission:
        search_conditions.append(Vehicle.transmission.ilike(f'%{transmission}%'))
    if fuel_type:
        search_conditions.append(Vehicle.fuel_type.ilike(f'%{fuel_type}%'))
    if condition:
        if condition.lower() == 'new':
            search_conditions.append(Vehicle.condition.ilike('New'))
        else:
            search_conditions.append(Vehicle.condition.ilike(f'%{condition}%'))

    # Retrieve vehicles based on search conditions
    vehicles_list = Vehicle.query.filter(*search_conditions).all()

    return render_template("vehicle_list.html", user=current_user,
                           vehicles=vehicles_list,
                           current_value=price_range,
                           selected_doors=num_doors,
                           selected_vehicle_type=vehicle_type,
                           selected_transmission=transmission,
                           selected_fuel_type=fuel_type,
                           selected_condition=condition,
                           search_query=search_query)
