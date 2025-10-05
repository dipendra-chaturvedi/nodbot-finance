from flask import Flask, render_template, session, redirect, url_for
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from config import Config
from utils.database import close_db, init_db

# Import blueprints
from routes.auth import auth_bp
from routes.loans import loans_bp
from routes.investments import investments_bp
from routes.payments import payments_bp
from routes.admin import admin_bp

# Create Flask app
app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
jwt = JWTManager(app)
bcrypt = Bcrypt(app)
CORS(app)

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(loans_bp, url_prefix='/loans')
app.register_blueprint(investments_bp, url_prefix='/investments')
app.register_blueprint(payments_bp, url_prefix='/payments')
app.register_blueprint(admin_bp, url_prefix='/admin')

# Close database connection after request
app.teardown_appcontext(close_db)

# Initialize database
with app.app_context():
    init_db()

@app.route('/')
def index():
    """Home page with role-based redirect"""
    if 'user_id' in session:
        # Redirect based on role
        if session.get('role') in ['admin', 'master', 'master_assistant']:
            return redirect(url_for('admin.admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))
    return redirect(url_for('auth.login'))

@app.route('/dashboard')
def dashboard():
    """User dashboard (for regular users only)"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # If admin/master, redirect to admin dashboard
    if session.get('role') in ['admin', 'master', 'master_assistant']:
        return redirect(url_for('admin.admin_dashboard'))
    
    # Get fresh user data from database
    from models.user import User
    user = User.find_by_id(session['user_id'])
    
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Update session with fresh data
    session['balance'] = float(user['balance'])
    session['username'] = user['username']
    session['email'] = user['email']
    session['role'] = user['role']
    
    return render_template('dashboard.html', user=user)

@app.context_processor
def inject_user():
    """Make user data available to all templates"""
    if 'user_id' in session:
        from models.user import User
        user = User.find_by_id(session['user_id'])
        if user:
            return dict(current_user=user)
    return dict(current_user=None)

@app.route('/routes')
def list_routes():
    """List all available routes (for development)"""
    routes = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            routes.append({
                'endpoint': rule.endpoint,
                'methods': ', '.join(rule.methods - {'HEAD', 'OPTIONS'}),
                'path': str(rule)
            })
    
    routes.sort(key=lambda x: x['path'])
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>NodBot Finance - API Routes</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { padding: 30px; background: #f5f7fa; }
            .route-card { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .badge-method { min-width: 70px; }
            h1 { color: #667eea; margin-bottom: 30px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 NodBot Finance - Available Routes</h1>
            <div class="row">
    """
    
    # Group routes by category
    categories = {
        'Authentication': [],
        'User Pages': [],
        'Admin Pages': [],
        'Loans API': [],
        'Investments API': [],
        'Payments API': [],
        'Admin API': [],
        'Other': []
    }
    
    for route in routes:
        path = route['path']
        if '/auth/' in path:
            categories['Authentication'].append(route)
        elif '/admin/api/' in path:
            categories['Admin API'].append(route)
        elif '/admin/' in path:
            categories['Admin Pages'].append(route)
        elif '/loans/api' in path:
            categories['Loans API'].append(route)
        elif '/loans/' in path:
            categories['User Pages'].append(route)
        elif '/investments/api' in path:
            categories['Investments API'].append(route)
        elif '/investments/' in path:
            categories['User Pages'].append(route)
        elif '/payments/api' in path:
            categories['Payments API'].append(route)
        elif '/payments/' in path:
            categories['User Pages'].append(route)
        else:
            categories['Other'].append(route)
    
    for category, routes_list in categories.items():
        if routes_list:
            html += f'<div class="col-md-6"><div class="route-card"><h5>{category}</h5><table class="table table-sm">'
            for route in routes_list:
                methods = route['methods'].split(', ')
                method_badges = ' '.join([f'<span class="badge bg-{"primary" if m == "GET" else "success" if m == "POST" else "warning" if m == "PUT" else "danger"} badge-method">{m}</span>' for m in methods])
                html += f'<tr><td>{method_badges}</td><td><code>{route["path"]}</code></td></tr>'
            html += '</table></div></div>'
    
    html += """
            </div>
        </div>
    </body>
    </html>
    """
    
    return html

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 NodBot Finance Flask App Starting...")
    print("="*60)
    print("\n📱 Application URLs:")
    print("   • Home:              http://localhost:5000")
    print("   • Login:             http://localhost:5000/auth/login")
    print("   • Register:          http://localhost:5000/auth/register")
    print("   • User Dashboard:    http://localhost:5000/dashboard")
    print("   • Admin Dashboard:   http://localhost:5000/admin/dashboard")
    print("\n📊 User Features:")
    print("   • Loans:             http://localhost:5000/loans/")
    print("   • Investments:       http://localhost:5000/investments/")
    print("   • Payments:          http://localhost:5000/payments/")
    print("\n👨‍💼 Admin Features:")
    print("   • Manage Loans:      http://localhost:5000/admin/loans")
    print("   • Manage Investments: http://localhost:5000/admin/investments")
    print("   • Manage Payments:   http://localhost:5000/admin/payments")
    print("   • Manage Users:      http://localhost:5000/admin/users")
    print("   • Settings:          http://localhost:5000/admin/settings")
    print("\n🔌 API Routes:")
    print("   • View All Routes:   http://localhost:5000/routes")
    print("\n👥 Test Accounts:")
    print("   • Admin:  admin@nodbot.com / admin123")
    print("   • User:   user@nodbot.com / user123")
    print("\n✨ Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    app.run(debug=True, port=5000, host='0.0.0.0')
