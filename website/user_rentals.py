from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from . import Renting, Vehicle, db

rentals_page = Blueprint('rentals_page', __name__)


@rentals_page.route('/rentals', methods=['GET'])
@login_required
def rentals():
    """
    User rentals page. Only accessible if user is logged in.

    """
    user_rentals = Renting.query.filter_by(user_id=current_user.id).all()
    rentals_with_vehicles = [
        {
            'rental': rental,
            'vehicle': Vehicle.query.get(rental.vehicle_id)
        } for rental in user_rentals
    ]
    return render_template('rentals.html', user=current_user, rentals=rentals_with_vehicles)


@rentals_page.route('/cancel_rental/<int:rental_id>', methods=['POST'])
@login_required
def cancel_rental(rental_id):
    """
    Cancels rental. Only accessible if user is logged in.
    :param rental_id:

    """
    rental = Renting.query.get_or_404(rental_id)
    if rental.user_id != current_user.id:
        flash('You do not have permission to cancel this rental.', 'danger')
        return redirect(url_for('rentals_page.rentals'))

    rental.is_active = False
    db.session.commit()
    flash('Rental cancelled successfully.', 'success')
    return redirect(url_for('rentals_page.rentals'))


@rentals_page.route('/remove_cancelled_rentals', methods=['POST'])
@login_required
def remove_cancelled_rentals():
    """
    Removes cancelled rentals. Only accessible if user is logged in.
    """
    cancelled_rentals = Renting.query.filter_by(user_id=current_user.id, is_active=False).all()

    if not cancelled_rentals:
        flash('No cancelled rentals to remove.', 'info')
        return redirect(url_for('rentals_page.rentals'))

    for rental in cancelled_rentals:
        db.session.delete(rental)

    db.session.commit()
    flash('Cancelled rentals removed successfully.', 'success')
    return redirect(url_for('rentals_page.rentals'))
