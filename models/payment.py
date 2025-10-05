from utils.database import get_db

class Payment:
    @staticmethod
    def transfer(sender_id, receiver_id, amount, reason):
        """Transfer money between users"""
        db = get_db()
        cursor = db.cursor()
        
        try:
            # Check sender balance
            cursor.execute("SELECT balance FROM users WHERE id = %s", (sender_id,))
            sender = cursor.fetchone()
            
            if not sender or sender['balance'] < amount:
                cursor.close()
                return None
            
            # Check receiver exists
            cursor.execute("SELECT id FROM users WHERE id = %s", (receiver_id,))
            receiver = cursor.fetchone()
            
            if not receiver:
                cursor.close()
                return None
            
            # Deduct from sender
            cursor.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (amount, sender_id))
            
            # Add to receiver
            cursor.execute("UPDATE users SET balance = balance + %s WHERE id = %s", (amount, receiver_id))
            
            # Record payment
            cursor.execute(
                """INSERT INTO payments (sender_id, receiver_id, amount, reason, transaction_type, status) 
                   VALUES (%s, %s, %s, %s, 'transfer', 'completed')""",
                (sender_id, receiver_id, amount, reason)
            )
            
            payment_id = cursor.lastrowid
            cursor.close()
            return payment_id
            
        except Exception as e:
            cursor.close()
            print(f"Transfer error: {e}")
            return None
    
    @staticmethod
    def get_all():
        """Get all payments with user details"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT p.*, 
                   s.username as sender_name, 
                   s.email as sender_email,
                   r.username as receiver_name,
                   r.email as receiver_email
            FROM payments p
            JOIN users s ON p.sender_id = s.id
            JOIN users r ON p.receiver_id = r.id
            ORDER BY p.created_at DESC
        """)
        payments = cursor.fetchall()
        cursor.close()
        return payments
    
    @staticmethod
    def get_by_user(user_id):
        """Get payments for specific user (sent or received)"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT p.*, 
                   s.username as sender_name, 
                   r.username as receiver_name 
            FROM payments p
            JOIN users s ON p.sender_id = s.id
            JOIN users r ON p.receiver_id = r.id
            WHERE p.sender_id = %s OR p.receiver_id = %s
            ORDER BY p.created_at DESC
        """, (user_id, user_id))
        payments = cursor.fetchall()
        cursor.close()
        return payments
    
    @staticmethod
    def get_by_id(payment_id):
        """Get payment by ID"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT p.*, 
                   s.username as sender_name,
                   r.username as receiver_name
            FROM payments p
            JOIN users s ON p.sender_id = s.id
            JOIN users r ON p.receiver_id = r.id
            WHERE p.id = %s
        """, (payment_id,))
        payment = cursor.fetchone()
        cursor.close()
        return payment
    
    @staticmethod
    def get_sent_by_user(user_id):
        """Get payments sent by user"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT p.*, r.username as receiver_name
            FROM payments p
            JOIN users r ON p.receiver_id = r.id
            WHERE p.sender_id = %s
            ORDER BY p.created_at DESC
        """, (user_id,))
        payments = cursor.fetchall()
        cursor.close()
        return payments
    
    @staticmethod
    def get_received_by_user(user_id):
        """Get payments received by user"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT p.*, s.username as sender_name
            FROM payments p
            JOIN users s ON p.sender_id = s.id
            WHERE p.receiver_id = %s
            ORDER BY p.created_at DESC
        """, (user_id,))
        payments = cursor.fetchall()
        cursor.close()
        return payments
    
    @staticmethod
    def get_total_sent(user_id):
        """Get total amount sent by user"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) as total
            FROM payments
            WHERE sender_id = %s AND status = 'completed'
        """, (user_id,))
        result = cursor.fetchone()
        cursor.close()
        return float(result['total']) if result else 0.0
    
    @staticmethod
    def get_total_received(user_id):
        """Get total amount received by user"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(amount), 0) as total
            FROM payments
            WHERE receiver_id = %s AND status = 'completed'
        """, (user_id,))
        result = cursor.fetchone()
        cursor.close()
        return float(result['total']) if result else 0.0
    
    @staticmethod
    def get_recent_transactions(user_id, limit=10):
        """Get recent transactions for user"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT p.*, 
                   s.username as sender_name,
                   r.username as receiver_name
            FROM payments p
            JOIN users s ON p.sender_id = s.id
            JOIN users r ON p.receiver_id = r.id
            WHERE p.sender_id = %s OR p.receiver_id = %s
            ORDER BY p.created_at DESC
            LIMIT %s
        """, (user_id, user_id, limit))
        payments = cursor.fetchall()
        cursor.close()
        return payments
