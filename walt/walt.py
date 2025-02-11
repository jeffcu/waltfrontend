# walt/walt.py

from flask import Blueprint, render_template

walt_bp = Blueprint('walt', __name__, template_folder='templates')

@walt_bp.route('/walt')
def walt_window():
    return render_template('walt_window.html')
