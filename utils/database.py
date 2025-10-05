from flask import g
import pymysql
from config import Config

def get_db():
    """Get database connection"""
    if 'db' not in g:
        g.db = pymysql.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            port=Config.MYSQL_PORT,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
    return g.db

def close_db(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize database tables (uses same structure as Node.js)"""
    db = get_db()
    cursor = db.cursor()
    
    # The tables are already created by your Node.js app
    # This function just ensures they exist
    
    try:
        # Check if tables exist
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        print(f"✅ Connected to database. Found {len(tables)} tables.")
    except Exception as e:
        print(f"❌ Database error: {e}")
    finally:
        cursor.close()
