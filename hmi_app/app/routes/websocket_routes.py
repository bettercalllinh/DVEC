from flask_socketio import emit

def register_events(socketio):
    """Register WebSocket event handlers"""

    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
        emit('connected', {'status': 'connected'})

    @socketio.on('disconnect')
    def handle_disconnect():
        print('Client disconnected')

    @socketio.on('payment_success')
    def handle_payment_success(data):
        """
        Handle payment success notification from payment portal.
        Broadcasts to all connected clients.
        """
        print(f'Payment success received: {data}')
        # Broadcast to all connected clients
        emit('payment_confirmed', {'status': 'success', 'data': data}, broadcast=True)

    @socketio.on('nfc_auth_result')
    def handle_nfc_auth_result(data):
        """
        Handle NFC authentication result.
        Broadcasts to all connected clients.
        """
        print(f'NFC auth result: {data}')
        emit('nfc_result', data, broadcast=True)
