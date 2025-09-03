# إعدادات الأمان
import os
from cryptography.fernet import Fernet

class SecurityConfig:
    """إعدادات الأمان للتطبيق"""
    
    @staticmethod
    def get_encryption_key():
        """الحصول على مفتاح التشفير"""
        key = os.getenv('ENCRYPTION_KEY')
        if not key:
            # إنشاء مفتاح جديد (فقط للتطوير)
            key = Fernet.generate_key()
            print("⚠️  تم إنشاء مفتاح تشفير جديد. تأكد من Saveه بأمان.")
        return key
    
    @staticmethod
    def encrypt_data(data):
        """تشفير البيانات"""
        if not data:
            return data
        
        try:
            key = SecurityConfig.get_encryption_key()
            f = Fernet(key)
            return f.encrypt(data.encode()).decode()
        except Exception:
            return data
    
    @staticmethod
    def decrypt_data(encrypted_data):
        """فك تشفير البيانات"""
        if not encrypted_data:
            return encrypted_data
        
        try:
            key = SecurityConfig.get_encryption_key()
            f = Fernet(key)
            return f.decrypt(encrypted_data.encode()).decode()
        except Exception:
            return encrypted_data
    
    @staticmethod
    def validate_input(data, max_length=255):
        """التحقق من صحة المدخلات"""
        if not data:
            return False
        
        if len(str(data)) > max_length:
            return False
        
        # التحقق من الأحرف الخطرة
        dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`', '$']
        for char in dangerous_chars:
            if char in str(data):
                return False
        
        return True
