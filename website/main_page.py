from flask import Blueprint, render_template
from flask_login import current_user

root = Blueprint('root', __name__)


@root.route('/')
def home():
    """
    Home page.
    """
    return render_template("home.html", user=current_user)
