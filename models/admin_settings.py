from utils.database import get_db

class AdminSettings:
    @staticmethod
    def get_all():
        """Get all admin settings"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM admin_settings ORDER BY setting_key")
        settings = cursor.fetchall()
        cursor.close()
        return settings
    
    @staticmethod
    def get(setting_key):
        """Get specific setting"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM admin_settings WHERE setting_key = %s", (setting_key,))
        setting = cursor.fetchone()
        cursor.close()
        return setting
    
    @staticmethod
    def set(setting_key, setting_value, description, updated_by):
        """Set or update setting"""
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute("""
            INSERT INTO admin_settings (setting_key, setting_value, description, updated_by)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                setting_value = VALUES(setting_value),
                description = VALUES(description),
                updated_by = VALUES(updated_by),
                updated_at = CURRENT_TIMESTAMP
        """, (setting_key, setting_value, description, updated_by))
        
        cursor.close()
        return True
    
    @staticmethod
    def delete(setting_key):
        """Delete setting"""
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM admin_settings WHERE setting_key = %s", (setting_key,))
        cursor.close()
        return True
