from flask import Flask, render_template

menu = Flask(__name__)

dropdown_visible = False


@menu.route('/toggle_dropdown')
def toggle_dropdown():
    """
    Toggles the visibility of the dropdown menu when it's pressed.
    """
    global dropdown_visible
    dropdown_visible = not dropdown_visible
    return render_template('base.html', dropdown_visible=dropdown_visible)
