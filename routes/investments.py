from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.investment import Investment
from models.user import User

investments_bp = Blueprint('investments', __name__)

@investments_bp.route('/', methods=['GET'])
def investments_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    return render_template('investments.html')

@investments_bp.route('/api', methods=['GET'])
@jwt_required()
def get_investments():
    current_user_id = get_jwt_identity()
    user = User.find_by_id(current_user_id)
    
    if user['role'] in ['admin', 'master', 'master_assistant']:
        investments = Investment.get_all()
    else:
        investments = Investment.get_by_user(current_user_id)
    
    return jsonify({'success': True, 'investments': investments})

@investments_bp.route('/api', methods=['POST'])
@jwt_required()
def create_investment():
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    # Check user balance
    user = User.find_by_id(current_user_id)
    if user['balance'] < data.get('amount'):
        return jsonify({'success': False, 'message': 'Insufficient balance'}), 400
    
    investment_id = Investment.create(
        current_user_id,
        data.get('investment_type'),
        data.get('amount'),
        data.get('frequency'),
        data.get('duration_months'),
        data.get('expected_return', 10.0)
    )
    
    return jsonify({'success': True, 'message': 'Investment created', 'investment_id': investment_id}), 201
