from flask import Blueprint, render_template, jsonify, request

bp = Blueprint('payment', __name__)

# VULNERABLE: Minimum deposit should be enforced server-side
MINIMUM_DEPOSIT = 20

# Store payment status for HMI polling (in-memory for demo)
payment_status = {
    'exploit_success': False,
    'amount': 0
}

@bp.route('/')
def index():
    """Serve the security lab page"""
    return render_template('payment.html')

@bp.route('/api/pay', methods=['POST'])
def process_payment():
    """
    VULNERABLE ENDPOINT - For educational purposes only!

    This endpoint demonstrates a common security flaw:
    - It accepts the payment amount from the client without validation
    - A secure implementation would enforce the minimum deposit server-side

    Vulnerability: Client-Side Trust
    CWE-602: Client-Side Enforcement of Server-Side Security
    """
    data = request.json or {}

    # VULNERABLE: Trusting client-provided amount!
    # This is intentionally insecure for the security lab
    amount = data.get('amount', MINIMUM_DEPOSIT)
    card = data.get('card', '')

    # Log the payment attempt (for demo purposes)
    print(f"[PAYMENT] Amount: ${amount}, Card: {card[-4:] if len(card) >= 4 else '****'}")

    # VULNERABLE: No server-side validation of amount!
    # A secure version would check: if amount < MINIMUM_DEPOSIT: return error

    # Track exploit success for HMI polling
    if amount < MINIMUM_DEPOSIT:
        payment_status['exploit_success'] = True
        payment_status['amount'] = amount
        print(f"[EXPLOIT] Successful! Amount: ${amount}")

    # Process payment (always succeeds for demo)
    return jsonify({
        'status': 'success',
        'message': 'Payment processed successfully',
        'amount_charged': amount,
        'transaction_id': 'TXN-' + str(hash(str(amount) + card) % 100000).zfill(5)
    })


@bp.route('/api/payment-status', methods=['GET'])
def get_payment_status():
    """
    API endpoint for HMI to poll payment status.
    Returns exploit success status and clears it after reading.
    """
    global payment_status

    if payment_status['exploit_success']:
        # Return success and clear the flag
        result = {
            'exploit_success': True,
            'amount': payment_status['amount']
        }
        # Reset status after HMI reads it
        payment_status['exploit_success'] = False
        payment_status['amount'] = 0
        return jsonify(result)

    return jsonify({
        'exploit_success': False,
        'amount': 0
    })


@bp.route('/api/reset-status', methods=['POST'])
def reset_status():
    """Reset payment status (for testing)"""
    global payment_status
    payment_status['exploit_success'] = False
    payment_status['amount'] = 0
    return jsonify({'status': 'reset'})

# This is how it SHOULD be implemented (commented out for the lab)
# @bp.route('/api/pay-secure', methods=['POST'])
# def process_payment_secure():
#     """
#     SECURE ENDPOINT - Proper implementation
#     """
#     data = request.json or {}
#
#     # SECURE: Ignore client amount, use server-defined minimum
#     amount = MINIMUM_DEPOSIT
#
#     # Or validate if amount is provided
#     client_amount = data.get('amount')
#     if client_amount is not None and client_amount < MINIMUM_DEPOSIT:
#         return jsonify({
#             'status': 'error',
#             'message': f'Minimum deposit is ${MINIMUM_DEPOSIT}'
#         }), 400
#
#     return jsonify({
#         'status': 'success',
#         'message': 'Payment processed successfully',
#         'amount_charged': MINIMUM_DEPOSIT
#     })
