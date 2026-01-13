from flask import Flask
from flask_socketio import SocketIO
from flask_cors import CORS

socketio = SocketIO(cors_allowed_origins="*")

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'damn-vulnerable-ev-charger-secret'

    CORS(app)
    socketio.init_app(app)

    from app.routes import nfc_routes, hmi_routes, websocket_routes
    app.register_blueprint(nfc_routes.bp)
    app.register_blueprint(hmi_routes.bp)

    # Register WebSocket events
    websocket_routes.register_events(socketio)

    return app

