from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.payment import Payment
from models.user import User

payments_bp = Blueprint('payments', __name__)

@payments_bp.route('/', methods=['GET'])
def payments_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('payments.html')

@payments_bp.route('/api', methods=['GET'])
@jwt_required()
def get_payments():
    current_user_id = get_jwt_identity()
    user = User.find_by_id(current_user_id)
    
    if user['role'] in ['admin', 'master', 'master_assistant']:
        payments = Payment.get_all()
    else:
        payments = Payment.get_by_user(current_user_id)
    
    return jsonify({'success': True, 'payments': payments})

@payments_bp.route('/api/transfer', methods=['POST'])
@jwt_required()
def transfer_money():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    receiver_id = data.get('receiver_id')
    amount = data.get('amount')
    reason = data.get('reason', '')
    
    # Validation
    if receiver_id == current_user_id:
        return jsonify({'success': False, 'message': 'Cannot send to yourself'}), 400
    
    user = User.find_by_id(current_user_id)
    if user['balance'] < amount:
        return jsonify({'success': False, 'message': 'Insufficient balance'}), 400
    
    receiver = User.find_by_id(receiver_id)
    if not receiver:
        return jsonify({'success': False, 'message': 'Receiver not found'}), 404
    
    payment_id = Payment.transfer(current_user_id, receiver_id, amount, reason)
    
    return jsonify({'success': True, 'message': 'Transfer successful', 'payment_id': payment_id})
