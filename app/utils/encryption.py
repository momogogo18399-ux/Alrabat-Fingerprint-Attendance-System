import bcrypt

def hash_password(plain_text_password: str) -> str:
    """
    يقوم بتشفير كلمة المرور باستخدام bcrypt.
    """
    # تحويل كلمة المرور إلى بايت
    password_bytes = plain_text_password.encode('utf-8')
    # إنشاء salt
    salt = bcrypt.gensalt()
    # تشفير البايتات
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    # إرجاعها كنص
    return hashed_bytes.decode('utf-8')

def check_password(plain_text_password: str, hashed_password: str) -> bool:
    """
    يتحقق مما إذا كانت كلمة المرور النصية تطابق النسخة المشفرة.
    """
    try:
        plain_bytes = plain_text_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except (ValueError, TypeError):
        # في حال كانت كلمة المرور المخزنة غير صالحة
        return False