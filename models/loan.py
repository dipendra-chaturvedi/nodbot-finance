from utils.database import get_db

class Loan:
    @staticmethod
    def create(user_id, loan_type, amount, term_months, interest_rate):
        """Create new loan request"""
        db = get_db()
        cursor = db.cursor()
        
        # Calculate monthly payment and total repayment
        monthly_rate = interest_rate / 100 / 12
        if monthly_rate > 0:
            monthly_payment = (amount * monthly_rate * (1 + monthly_rate) ** term_months) / \
                             ((1 + monthly_rate) ** term_months - 1)
        else:
            monthly_payment = amount / term_months
            
        total_repayment = monthly_payment * term_months
        
        cursor.execute(
            """INSERT INTO loans (user_id, loan_type, amount, interest_rate, term_months, 
               monthly_payment, total_repayment, status) 
               VALUES (%s, %s, %s, %s, %s, %s, %s, 'pending')""",
            (user_id, loan_type, amount, interest_rate, term_months, monthly_payment, total_repayment)
        )
        
        loan_id = cursor.lastrowid
        cursor.close()
        return loan_id
    
    @staticmethod
    def get_all():
        """Get all loans with user details"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT l.*, u.username, u.email 
            FROM loans l 
            JOIN users u ON l.user_id = u.id
            ORDER BY l.created_at DESC
        """)
        loans = cursor.fetchall()
        cursor.close()
        return loans
    
    @staticmethod
    def get_by_user(user_id):
        """Get loans for specific user"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT l.*, u.username 
            FROM loans l 
            JOIN users u ON l.user_id = u.id 
            WHERE l.user_id = %s
            ORDER BY l.created_at DESC
        """, (user_id,))
        loans = cursor.fetchall()
        cursor.close()
        return loans
    
    @staticmethod
    def get_by_id(loan_id):
        """Get loan by ID"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM loans WHERE id = %s", (loan_id,))
        loan = cursor.fetchone()
        cursor.close()
        return loan
    
    @staticmethod
    def approve(loan_id, approved_by):
        """Approve loan and credit user account"""
        db = get_db()
        cursor = db.cursor()
        
        # Get loan details
        cursor.execute("SELECT * FROM loans WHERE id = %s", (loan_id,))
        loan = cursor.fetchone()
        
        if loan and loan['status'] == 'pending':
            # Update loan status
            cursor.execute(
                "UPDATE loans SET status = 'approved', approved_by = %s WHERE id = %s",
                (approved_by, loan_id)
            )
            
            # Add amount to user balance
            cursor.execute(
                "UPDATE users SET balance = balance + %s WHERE id = %s",
                (loan['amount'], loan['user_id'])
            )
            
            # Record payment transaction
            cursor.execute(
                """INSERT INTO payments (sender_id, receiver_id, amount, reason, transaction_type, status) 
                   VALUES (%s, %s, %s, %s, 'loan_repayment', 'completed')""",
                (approved_by, loan['user_id'], loan['amount'], f"Loan approved: {loan['loan_type']}")
            )
        
        cursor.close()
        return True
    
    @staticmethod
    def reject(loan_id):
        """Reject loan"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("UPDATE loans SET status = 'rejected' WHERE id = %s", (loan_id,))
        cursor.close()
        return True
    
    @staticmethod
    def repay(loan_id, user_id, amount):
        """Make loan repayment"""
        db = get_db()
        cursor = db.cursor()
        
        # Get loan details
        cursor.execute("SELECT * FROM loans WHERE id = %s AND user_id = %s", (loan_id, user_id))
        loan = cursor.fetchone()
        
        if not loan:
            cursor.close()
            return False
        
        # Check user balance
        cursor.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
        
        if user['balance'] < amount:
            cursor.close()
            return False
        
        # Update loan payment
        new_paid = float(loan['amount_paid']) + float(amount)
        cursor.execute("UPDATE loans SET amount_paid = %s WHERE id = %s", (new_paid, loan_id))
        
        # Deduct from user balance
        cursor.execute("UPDATE users SET balance = balance - %s WHERE id = %s", (amount, user_id))
        
        # Check if loan is fully paid
        if new_paid >= float(loan['total_repayment']):
            cursor.execute("UPDATE loans SET status = 'paid' WHERE id = %s", (loan_id,))
        
        cursor.close()
        return True
    
    @staticmethod
    def get_pending_count():
        """Get count of pending loans"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM loans WHERE status = 'pending'")
        result = cursor.fetchone()
        cursor.close()
        return result['count'] if result else 0
