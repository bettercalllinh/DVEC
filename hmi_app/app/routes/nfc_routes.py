from flask import Blueprint, jsonify, request
import os

bp = Blueprint('nfc', __name__, url_prefix='/api/nfc')

# Global queue for NFC events (for polling)
nfc_event_queue = []


def get_valid_uids_file():
    """Get the path to valid_uid.txt"""
    return os.path.join(os.path.dirname(__file__), '..', '..', 'valid_uid.txt')


def load_valid_uids():
    """Load valid UIDs from valid_uid.txt"""
    uid_file = get_valid_uids_file()
    try:
        with open(uid_file, 'r') as f:
            uids = []
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    uids.append(line.upper())
            return uids
    except FileNotFoundError:
        return []


def validate_uid(uid):
    """Check if UID exists in valid_uid.txt"""
    if not uid:
        return False
    valid_uids = load_valid_uids()
    return uid.upper() in valid_uids


def nfc_event_callback(uid, is_valid):
    """
    Callback function called by NFCReader when a card is detected.
    Pushes event to the queue for frontend polling and emits via WebSocket.
    """
    global nfc_event_queue
    event = {
        "type": "valid" if is_valid else "invalid",
        "uid": uid
    }
    nfc_event_queue.append(event)

    # Also emit via WebSocket for real-time updates
    try:
        from app import socketio
        socketio.emit('nfc_result', event)
        print(f"[NFC] Emitted event via WebSocket: {event}")
    except Exception as e:
        print(f"[NFC] WebSocket emit failed: {e}")

@bp.route('/poll', methods=['GET'])
def poll_nfc():
    """Frontend polls this to check for NFC events"""
    global nfc_event_queue
    if nfc_event_queue:
        event = nfc_event_queue.pop(0)
        return jsonify({"event": event})
    return jsonify({"event": None})

@bp.route('/simulate', methods=['POST'])
def simulate_nfc():
    """Simulate NFC card swipe for testing"""
    data = request.get_json() or {}
    uid = data.get('uid', '')

    is_valid = validate_uid(uid)
    uid_str = uid.upper() if uid else "EMPTY"

    # Use the callback which handles both queue and WebSocket
    nfc_event_callback(uid_str, is_valid)

    return jsonify({"status": "ok", "valid": is_valid, "uid": uid_str})

@bp.route('/auth', methods=['POST'])
def nfc_auth():
    """
    NFC authentication flow:
    1. Receive NFC UID from request
    2. Validate against valid_uid.txt
    3. Return success/failure
    """
    data = request.get_json() or {}
    nfc_uid = data.get('nfc_uid', '')

    if not nfc_uid:
        return jsonify({
            "status": 400,
            "message": "NFC UID required",
            "valid": False
        }), 400

    if validate_uid(nfc_uid):
        return jsonify({
            "status": 200,
            "message": "Authentication successful - Ready to charge",
            "valid": True,
            "uid": nfc_uid.upper()
        })
    else:
        return jsonify({
            "status": 401,
            "message": "Authentication failed - Invalid card",
            "valid": False,
            "uid": nfc_uid.upper()
        }), 401

@bp.route('/valid-uids', methods=['GET'])
def get_valid_uids():
    """Get list of valid UIDs (for demo/debug purposes)"""
    return jsonify({
        "uids": load_valid_uids()
    })


@bp.route('/status', methods=['GET'])
def nfc_status():
    """Get NFC reader hardware status"""
    try:
        from app.services.nfc_reader import is_hardware_available, get_reader
        reader = get_reader()
        return jsonify({
            "hardware_available": is_hardware_available(),
            "reader_running": reader.running if reader else False,
            "valid_uids_count": len(load_valid_uids())
        })
    except ImportError:
        return jsonify({
            "hardware_available": False,
            "reader_running": False,
            "valid_uids_count": len(load_valid_uids()),
            "error": "NFC reader service not available"
        })


@bp.route('/reload-uids', methods=['POST'])
def reload_uids():
    """Reload valid UIDs from file"""
    try:
        from app.services.nfc_reader import get_reader
        reader = get_reader()
        if reader:
            reader.reload_valid_uids()
        return jsonify({
            "status": "ok",
            "uids_count": len(load_valid_uids())
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

