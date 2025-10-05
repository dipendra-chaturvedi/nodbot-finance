from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from utils.database import get_db

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        verify_jwt_in_request()
        return f(*args, **kwargs)
    return decorated

def role_required(*allowed_roles):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            verify_jwt_in_request()
            current_user_id = get_jwt_identity()
            
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT role FROM users WHERE id = %s", (current_user_id,))
            user = cursor.fetchone()
            cursor.close()
            
            if not user or user['role'] not in allowed_roles:
                return jsonify({'success': False, 'message': 'Access denied'}), 403
                
            return f(*args, **kwargs)
        return decorated
    return wrapper
