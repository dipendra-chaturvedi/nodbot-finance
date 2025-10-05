import os
from datetime import timedelta

class Config:
    # MySQL Database Configuration (same as Node.js project)
    MYSQL_HOST = os.getenv('DB_HOST', 'localhost')
    MYSQL_USER = os.getenv('DB_USER', 'root')
    MYSQL_PASSWORD = os.getenv('DB_PASSWORD', '')
    MYSQL_DB = os.getenv('DB_NAME', 'nodbot_finance')
    MYSQL_PORT = int(os.getenv('DB_PORT', 3306))
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET', 'your-secret-key-here')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'flask-secret-key')
    DEBUG = os.getenv('DEBUG', 'True') == 'True'
