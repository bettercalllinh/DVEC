from flask import Blueprint, render_template

bp = Blueprint('hmi', __name__)

@bp.route('/')
def index():
    """Serve the main HMI single-page application"""
    return render_template('index.html')
