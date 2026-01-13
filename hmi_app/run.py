from app import create_app, socketio

app = create_app()

if __name__ == '__main__':
    print("Starting HMI Server on http://localhost:8080")
    socketio.run(app, host='0.0.0.0', port=8080, debug=True, allow_unsafe_werkzeug=True)

