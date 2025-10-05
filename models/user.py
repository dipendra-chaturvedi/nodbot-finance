from utils.database import get_db
from flask_bcrypt import generate_password_hash, check_password_hash

class User:
    @staticmethod
    def create(username, email, password, role='user', initial_balance=0.0):
        """Create new user with optional initial balance"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            # Check if user already exists
            cursor.execute("SELECT id FROM users WHERE email = %s OR username = %s", (email, username))
            existing_user = cursor.fetchone()
            
            if existing_user:
                cursor.close()
                return None
            
            # Hash password
            hashed_password = generate_password_hash(password).decode('utf-8')
            
            # Insert user with initial balance
            cursor.execute(
                """INSERT INTO users (username, email, password, role, balance) 
                   VALUES (%s, %s, %s, %s, %s)""",
                (username, email, hashed_password, role, initial_balance)
            )
            
            user_id = cursor.lastrowid
            cursor.close()
            return user_id
            
        except Exception as e:
            cursor.close()
            print(f"Error creating user: {e}")
            return None
    
    @staticmethod
    def find_by_email(email):
        """Find user by email"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()
        return user
    
    @staticmethod
    def find_by_username(username):
        """Find user by username"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        return user
    
    @staticmethod
    def find_by_id(user_id):
        """Find user by ID"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        cursor.close()
        return user
    
    @staticmethod
    def verify_password(stored_password, provided_password):
        """Verify password"""
        return check_password_hash(stored_password, provided_password)
    
    @staticmethod
    def get_all():
        """Get all users (excluding passwords)"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            cursor.execute("""
                SELECT id, username, email, role, balance, created_at, updated_at 
                FROM users 
                ORDER BY created_at DESC
            """)
            users = cursor.fetchall()
            cursor.close()
            return users
        except Exception as e:
            print(f"Error getting users: {e}")
            cursor.close()
            return []

        
        @staticmethod
        def update_balance(user_id, new_balance):
            """Update user balance"""
            db = get_db()
            cursor = db.cursor()
            cursor.execute("UPDATE users SET balance = %s WHERE id = %s", (new_balance, user_id))
            cursor.close()
            return True
    
    @staticmethod
    def get_balance(user_id):
        """Get user balance"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
        result = cursor.fetchone()
        cursor.close()
        return float(result['balance']) if result else 0.0
    
    @staticmethod
    def update_profile(user_id, username=None, email=None):
        """Update user profile"""
        db = get_db()
        cursor = db.cursor()
        
        if username:
            cursor.execute("UPDATE users SET username = %s WHERE id = %s", (username, user_id))
        
        if email:
            cursor.execute("UPDATE users SET email = %s WHERE id = %s", (email, user_id))
        
        cursor.close()
        return True
    
    @staticmethod
    def change_password(user_id, new_password):
        """Change user password"""
        db = get_db()
        cursor = db.cursor()
        
        hashed_password = generate_password_hash(new_password).decode('utf-8')
        cursor.execute("UPDATE users SET password = %s WHERE id = %s", (hashed_password, user_id))
        
        cursor.close()
        return True
    
    @staticmethod
    def delete_user(user_id):
        """Delete user (admin only)"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        cursor.close()
        return True
    
    @staticmethod
    def get_user_stats(user_id):
        """Get user statistics"""
        db = get_db()
        cursor = db.cursor()
        
        # Get loan stats
        cursor.execute("""
            SELECT COUNT(*) as total_loans, 
                   COALESCE(SUM(amount), 0) as total_loan_amount,
                   COALESCE(SUM(amount_paid), 0) as total_paid
            FROM loans WHERE user_id = %s
        """, (user_id,))
        loan_stats = cursor.fetchone()
        
        # Get investment stats
        cursor.execute("""
            SELECT COUNT(*) as total_investments, 
                   COALESCE(SUM(amount), 0) as total_investment_amount,
                   COALESCE(SUM(maturity_amount), 0) as expected_returns
            FROM investments WHERE user_id = %s
        """, (user_id,))
        investment_stats = cursor.fetchone()
        
        # Get payment stats
        cursor.execute("""
            SELECT COUNT(*) as total_transactions,
                   COALESCE(SUM(CASE WHEN sender_id = %s THEN amount ELSE 0 END), 0) as total_sent,
                   COALESCE(SUM(CASE WHEN receiver_id = %s THEN amount ELSE 0 END), 0) as total_received
            FROM payments WHERE sender_id = %s OR receiver_id = %s
        """, (user_id, user_id, user_id, user_id))
        payment_stats = cursor.fetchone()
        
        cursor.close()
        
        return {
            'loans': loan_stats,
            'investments': investment_stats,
            'payments': payment_stats
        }
