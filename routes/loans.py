from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.loan import Loan
from models.user import User

loans_bp = Blueprint('loans', __name__)

@loans_bp.route('/', methods=['GET'])
def loans_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('loans.html')

@loans_bp.route('/api', methods=['GET'])
@jwt_required()
def get_loans():
    current_user_id = get_jwt_identity()
    user = User.find_by_id(current_user_id)
    
    if user['role'] in ['admin', 'master', 'master_assistant']:
        loans = Loan.get_all()
    else:
        loans = Loan.get_by_user(current_user_id)
    
    return jsonify({'success': True, 'loans': loans})

@loans_bp.route('/api', methods=['POST'])
@jwt_required()
def create_loan():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    loan_id = Loan.create(
        current_user_id,
        data.get('loan_type'),
        data.get('amount'),
        data.get('term_months'),
        data.get('interest_rate', 10.0)
    )
    
    return jsonify({'success': True, 'message': 'Loan created', 'loan_id': loan_id}), 201

@loans_bp.route('/api/repay', methods=['POST'])
@jwt_required()
def repay_loan():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    loan_id = data.get('loan_id')
    amount = data.get('amount')
    
    from utils.database import get_db
    db = get_db()
    cursor = db.cursor()
    
    # Get loan details
    cursor.execute("SELECT * FROM loans WHERE id = %s AND user_id = %s", (loan_id, current_user_id))
    loan = cursor.fetchone()
    
    if not loan:
        return jsonify({'success': False, 'message': 'Loan not found'}), 404
    
    # Check user balance
    cursor.execute("SELECT balance FROM users WHERE id = %s", (current_user_id,))
    user = cursor.fetchone()
    
    if user['balance'] < amount:
        return jsonify({'success': False, 'message': 'Insufficient balance'}), 400
    
    # Update loan
    new_paid = float(loan['amount_paid']) + float(amount)
    cursor.execute("UPDATE loans SET amount_paid = %s WHERE id = %s", (new_paid, loan_id))
    
    # Update user balance
    cursor.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (amount, current_user_id))
    
    # Check if fully paid
    if new_paid >= float(loan['total_repayment']):
        cursor.execute("UPDATE loans SET status = 'paid' WHERE id = %s", (loan_id,))
    
    cursor.close()
    
    remaining = float(loan['total_repayment']) - new_paid
    
    return jsonify({'success': True, 'message': 'Payment successful', 'remaining': max(0, remaining)})
