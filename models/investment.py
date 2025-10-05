from utils.database import get_db
from datetime import datetime, timedelta

class Investment:
    @staticmethod
    def create(user_id, investment_type, amount, frequency, duration_months, expected_return):
        """Create new investment"""
        db = get_db()
        cursor = db.cursor()
        
        # Calculate maturity amount and date
        maturity_amount = amount * (1 + (expected_return / 100) * (duration_months / 12))
        maturity_date = datetime.now() + timedelta(days=duration_months * 30)
        
        # Check user balance
        cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if not user or user['balance'] < amount:
            cursor.close()
            return None
        
        # Insert investment
        cursor.execute(
            """INSERT INTO investments (user_id, investment_type, amount, frequency, 
               duration_months, expected_return, maturity_amount, maturity_date, status) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'active')""",
            (user_id, investment_type, amount, frequency, duration_months, 
             expected_return, maturity_amount, maturity_date)
        )
        
        # Deduct from user balance
        cursor.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (amount, user_id))
        
        investment_id = cursor.lastrowid
        cursor.close()
        return investment_id
    
    @staticmethod
    def get_all():
        """Get all investments with user details"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT i.*, u.username, u.email 
            FROM investments i 
            JOIN users u ON i.user_id = u.id
            ORDER BY i.created_at DESC
        """)
        investments = cursor.fetchall()
        cursor.close()
        return investments
    
    @staticmethod
    def get_by_user(user_id):
        """Get investments for specific user"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT * FROM investments 
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (user_id,))
        investments = cursor.fetchall()
        cursor.close()
        return investments
    
    @staticmethod
    def get_by_id(investment_id):
        """Get investment by ID"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM investments WHERE id = %s", (investment_id,))
        investment = cursor.fetchone()
        cursor.close()
        return investment
    
    @staticmethod
    def update_status(investment_id, status):
        """Update investment status"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE investments SET status = %s WHERE id = %s", (status, investment_id))
        cursor.close()
        return True
    
    @staticmethod
    def mature_investment(investment_id):
        """Mature investment and credit maturity amount"""
        db = get_db()
        cursor = db.cursor()
        
        # Get investment details
        cursor.execute("SELECT * FROM investments WHERE id = %s", (investment_id,))
        investment = cursor.fetchone()
        
        if investment and investment['status'] == 'active':
            # Update status
            cursor.execute("UPDATE investments SET status = 'matured' WHERE id = %s", (investment_id,))
            
            # Credit maturity amount to user
            cursor.execute(
                "UPDATE users SET balance = balance + %s WHERE id = %s",
                (investment['maturity_amount'], investment['user_id'])
            )
        
        cursor.close()
        return True
    
    @staticmethod
    def cancel_investment(investment_id, user_id):
        """Cancel investment and refund amount"""
        db = get_db()
        cursor = db.cursor()
        
        # Get investment details
        cursor.execute("SELECT * FROM investments WHERE id = %s AND user_id = %s", (investment_id, user_id))
        investment = cursor.fetchone()
        
        if investment and investment['status'] == 'active':
            # Update status
            cursor.execute("UPDATE investments SET status = 'cancelled' WHERE id = %s", (investment_id,))
            
            # Refund amount to user (minus penalty if any)
            refund_amount = float(investment['amount']) * 0.95  # 5% penalty
            cursor.execute(
                "UPDATE users SET balance = balance + %s WHERE id = %s",
                (refund_amount, user_id)
            )
        
        cursor.close()
        return True
    
    @staticmethod
    def get_active_count():
        """Get count of active investments"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM investments WHERE status = 'active'")
        result = cursor.fetchone()
        cursor.close()
        return result['count'] if result else 0
