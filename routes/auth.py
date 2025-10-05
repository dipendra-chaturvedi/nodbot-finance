from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')
        initial_balance = float(data.get('initial_balance', 0.0))
        
        # Validation
        if not username or not email or not password:
            return jsonify({
                'success': False, 
                'message': 'Username, email and password are required'
            }), 400
        
        if len(password) < 6:
            return jsonify({
                'success': False, 
                'message': 'Password must be at least 6 characters long'
            }), 400
        
        # Check if user already exists
        existing_user = User.find_by_email(email)
        if existing_user:
            return jsonify({
                'success': False, 
                'message': 'Email already registered'
            }), 400
        
        existing_username = User.find_by_username(username)
        if existing_username:
            return jsonify({
                'success': False, 
                'message': 'Username already taken'
            }), 400
        
        # Create user
        user_id = User.create(username, email, password, role, initial_balance)
        
        if user_id:
            return jsonify({
                'success': True,
                'message': 'User registered successfully',
                'user_id': user_id
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': 'Registration failed. Please try again.'
            }), 500
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login with role-based redirection"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                'success': False, 
                'message': 'Email and password are required'
            }), 400
        
        user = User.find_by_email(email)
        
        if not user or not User.verify_password(user['password'], password):
            return jsonify({
                'success': False, 
                'message': 'Invalid email or password'
            }), 401
        
        # Create access token
        access_token = create_access_token(identity=user['id'])
        
        # Store in session for web interface
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['email'] = user['email']
        session['balance'] = float(user['balance'])
        
        # Role-based redirect URL
        redirect_url = '/'
        if user['role'] in ['admin', 'master', 'master_assistant']:
            redirect_url = '/admin/dashboard'
        else:
            redirect_url = '/dashboard'
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': access_token,
            'redirect_url': redirect_url,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'balance': float(user['balance'])
            }
        })
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/me')
@jwt_required()
def get_current_user():
    """Get current logged-in user details"""
    current_user_id = get_jwt_identity()
    user = User.find_by_id(current_user_id)
    
    if user:
        # Remove password from response
        user_data = dict(user)
        user_data.pop('password', None)
        
        # Get user statistics
        stats = User.get_user_stats(current_user_id)
        user_data['stats'] = stats
        
        return jsonify({'success': True, 'user': user_data})
    
    return jsonify({'success': False, 'message': 'User not found'}), 404
@auth_bp.route('/refresh-session', methods=['POST'])
@jwt_required()
def refresh_session():
    """Refresh session data"""
    current_user_id = get_jwt_identity()
    user = User.find_by_id(current_user_id)
    
    if user:
        # Update session with fresh data
        session['balance'] = float(user['balance'])
        session['username'] = user['username']
        session['email'] = user['email']
        session['role'] = user['role']
        
        return jsonify({
            'success': True,
            'message': 'Session refreshed',
            'balance': float(user['balance'])
        })
    
    return jsonify({'success': False, 'message': 'User not found'}), 404
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, session, flash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        role = data.get('role', 'user')
        initial_balance = float(data.get('initial_balance', 0.0))
        
        if not username or not email or not password:
            return jsonify({'success': False, 'message': 'All fields required'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': 'Password must be 6+ characters'}), 400
        
        if User.find_by_email(email):
            return jsonify({'success': False, 'message': 'Email already registered'}), 400
        
        if User.find_by_username(username):
            return jsonify({'success': False, 'message': 'Username already taken'}), 400
        
        user_id = User.create(username, email, password, role, initial_balance)
        
        if user_id:
            return jsonify({'success': True, 'message': 'Registration successful', 'user_id': user_id}), 201
        else:
            return jsonify({'success': False, 'message': 'Registration failed'}), 500
    
    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password required'}), 400
        
        user = User.find_by_email(email)
        
        if not user or not User.verify_password(user['password'], password):
            return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
        
        access_token = create_access_token(identity=user['id'])
        
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        session['email'] = user['email']
        session['balance'] = float(user['balance'])
        
        redirect_url = '/admin/dashboard' if user['role'] in ['admin', 'master', 'master_assistant'] else '/dashboard'
        
        return jsonify({
            'success': True,
            'message': 'Login successful',
            'token': access_token,
            'redirect_url': redirect_url,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role'],
                'balance': float(user['balance'])
            }
        })
    
    return render_template('login.html')

@auth_bp.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/me')
@jwt_required()
def get_current_user():
    """Get current user"""
    current_user_id = get_jwt_identity()
    user = User.find_by_id(current_user_id)
    
    if user:
        user_data = dict(user)
        user_data.pop('password', None)
        stats = User.get_user_stats(current_user_id)
        user_data['stats'] = stats
        return jsonify({'success': True, 'user': user_data})
    
    return jsonify({'success': False, 'message': 'User not found'}), 404

@auth_bp.route('/refresh-session', methods=['POST'])
@jwt_required()
def refresh_session():
    """Refresh session"""
    current_user_id = get_jwt_identity()
    user = User.find_by_id(current_user_id)
    
    if user:
        session['balance'] = float(user['balance'])
        session['username'] = user['username']
        session['email'] = user['email']
        session['role'] = user['role']
        
        return jsonify({'success': True, 'message': 'Session refreshed', 'balance': float(user['balance'])})
    
    return jsonify({'success': False, 'message': 'User not found'}), 404
