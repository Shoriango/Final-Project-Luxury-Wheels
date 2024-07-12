from flask import Blueprint, render_template, request, flash, redirect, url_for
from . import User, db
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, login_required, logout_user, current_user
from phonenumbers import is_possible_number, parse

auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login page. Only accessible if user is not logged in.
    """
    if current_user.is_authenticated:
        return redirect(url_for('root.home'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in', category='success')
                login_user(user, remember=True)
                return redirect(url_for('root.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    """
    Sign up page. Only accessible if user is not logged in.
    Gets email, first name, password, phone number and user type.
    User type can be either business or personal.
    """
    if current_user.is_authenticated:
        return redirect(url_for('root.home'))
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        phone_number = request.form.get('phone')
        user_type = request.form.get('user_type')

        if '+' not in phone_number:
            phone_number = '+351' + phone_number

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters', category='error')

        elif len(first_name) < 2:
            flash('First Name must be greater than 1 character',
                  category='error')

        elif password1 != password2:
            flash("Passwords don't much", category='error')

        elif len(password1) < 7:
            flash("Passwords must be atleast 7 characters", category='error')

        elif not is_possible_number(parse(phone_number.strip())):
            flash("Number must be valid", category='error')

        else:
            new_user = User(email=email, first_name=first_name,
                            password=generate_password_hash(password1),
                            phone_number=phone_number, user_type=user_type)
            db.session.add(new_user)
            db.session.commit()
            flash('Account created, please log in', category='success')
            return redirect(url_for('auth.login'))

    return render_template("sign_up.html", user=current_user)
