from flask import Flask
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'payment-portal-secret'

    CORS(app)

    from app.routes import payment_routes
    app.register_blueprint(payment_routes.bp)

    return app
