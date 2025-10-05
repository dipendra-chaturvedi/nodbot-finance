from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for, flash
from flask_jwt_extended import jwt_required, get_jwt_identity
from models.user import User
from models.loan import Loan
from models.investment import Investment
from models.payment import Payment
from utils.decorators import role_required
from utils.database import get_db

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/')
@admin_bp.route('/dashboard')
def admin_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if session.get('role') not in ['admin', 'master', 'master_assistant']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('admin/dashboard.html')

@admin_bp.route('/loans')
def admin_loans():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if session.get('role') not in ['admin', 'master', 'master_assistant']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('admin/loans.html')

@admin_bp.route('/investments')
def admin_investments():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if session.get('role') not in ['admin', 'master', 'master_assistant']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('admin/investments.html')

@admin_bp.route('/payments')
def admin_payments():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if session.get('role') not in ['admin', 'master', 'master_assistant']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('admin/payments.html')

@admin_bp.route('/users')
def users_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if session.get('role') not in ['admin', 'master', 'master_assistant']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('admin/users.html')

@admin_bp.route('/settings')
def settings_page():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    if session.get('role') not in ['admin', 'master']:
        flash('Access denied', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('admin/settings.html')

# API Routes
@admin_bp.route('/api/dashboard-stats', methods=['GET'])
@jwt_required()
@role_required('admin', 'master', 'master_assistant')
def get_dashboard_stats():
    db = get_db()
    cursor = db.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM users")
    total_users = cursor.fetchone()['total']
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_loans,
            SUM(amount) as total_amount,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved,
            SUM(CASE WHEN status = 'paid' THEN 1 ELSE 0 END) as paid
        FROM loans
    """)
    loan_stats = cursor.fetchone()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_investments,
            SUM(amount) as total_amount,
            SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN status = 'matured' THEN 1 ELSE 0 END) as matured
        FROM investments
    """)
    investment_stats = cursor.fetchone()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_transactions,
            SUM(amount) as total_amount,
            SUM(CASE WHEN created_at >= DATE_SUB(NOW(), INTERVAL 30 DAY) THEN amount ELSE 0 END) as monthly_volume
        FROM payments
    """)
    payment_stats = cursor.fetchone()
    
    cursor.execute("""
        SELECT 'loan' as type, l.id, u.username, l.amount, l.status, l.created_at
        FROM loans l
        JOIN users u ON l.user_id = u.id
        ORDER BY l.created_at DESC
        LIMIT 10
    """)
    recent_activity = cursor.fetchall()
    
    cursor.close()
    
    return jsonify({
        'success': True,
        'stats': {
            'users': {'total': total_users, 'regular': 0, 'admins': 0},
            'loans': loan_stats,
            'investments': investment_stats,
            'payments': payment_stats,
            'recent_activity': recent_activity
        }
    })

@admin_bp.route('/api/loans/all', methods=['GET'])
@jwt_required()
@role_required('admin', 'master', 'master_assistant')
def get_all_loans():
    loans = Loan.get_all()
    return jsonify({'success': True, 'loans': loans})

@admin_bp.route('/api/loans/<int:loan_id>/approve', methods=['POST'])
@jwt_required()
@role_required('admin', 'master')
def approve_loan_admin(loan_id):
    current_user_id = get_jwt_identity()
    Loan.approve(loan_id, current_user_id)
    return jsonify({'success': True, 'message': 'Loan approved'})

@admin_bp.route('/api/investments/all', methods=['GET'])
@jwt_required()
@role_required('admin', 'master', 'master_assistant')
def get_all_investments():
    investments = Investment.get_all()
    return jsonify({'success': True, 'investments': investments})

@admin_bp.route('/api/payments/all', methods=['GET'])
@jwt_required()
@role_required('admin', 'master', 'master_assistant')
def get_all_payments():
    payments = Payment.get_all()
    return jsonify({'success': True, 'payments': payments})


@admin_bp.route('/api/users', methods=['GET'])
@jwt_required()
@role_required('admin', 'master', 'master_assistant')
def get_all_users():
    """Get all users"""
    print("🔍 GET /admin/api/users called")
    
    try:
        users = User.get_all()
        print(f"✅ Found {len(users)} users in database")
        
        # Add stats for each user
        for user in users:
            stats = User.get_user_stats(user['id'])
            user['stats'] = stats
        
        print(f"✅ Returning {len(users)} users")
        return jsonify({'success': True, 'users': users, 'total': len(users)})
    
    except Exception as e:
        print(f"❌ Error getting users: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
