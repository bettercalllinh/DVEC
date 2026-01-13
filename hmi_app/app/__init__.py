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

    # Initialize NFC reader service (only starts if hardware is available)
    with app.app_context():
        try:
            from app.services.nfc_reader import init_reader
            from app.routes.nfc_routes import nfc_event_callback
            init_reader(event_callback=nfc_event_callback)
        except Exception as e:
            app.logger.warning(f"NFC reader initialization skipped: {e}")

    return app

