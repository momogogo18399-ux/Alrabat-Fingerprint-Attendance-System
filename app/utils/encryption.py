import bcrypt

def hash_password(plain_text_password: str) -> str:
    """
    يقوم بتشفير كلمة المرور كنص عادي باستخدام خوارزمية bcrypt الآمنة.

    Args:
        plain_text_password: كلمة المرور المراد تشفيرها.

    Returns:
        النسخة المشفرة من كلمة المرور كنص (string).
    """
    # تحويل كلمة المرور من نص إلى بايتات (bytes) باستخدام ترميز utf-8
    password_bytes = plain_text_password.encode('utf-8')
    
    # إنشاء "ملح" (salt) عشوائي لزيادة الأمان
    salt = bcrypt.gensalt()
    
    # تشفير البايتات باستخدام الملح
    hashed_bytes = bcrypt.hashpw(password_bytes, salt)
    
    # إرجاع النسخة المشفرة كنص لسهولة تخزينها في قاعدة البيانات
    return hashed_bytes.decode('utf-8')

def check_password(plain_text_password: str, hashed_password: str) -> bool:
    """
    يتحقق مما إذا كانت كلمة المرور النصية المدخلة تطابق النسخة المشفرة المخزنة.

    Args:
        plain_text_password: كلمة المرور التي أدخلها المستخدم.
        hashed_password: كلمة المرور المشفرة من قاعدة البيانات.

    Returns:
        True إذا تطابقت كلمات المرور، و False إذا لم تتطابق.
    """
    try:
        # تحويل كلا من كلمة المرور النصية والمشفرة إلى بايتات
        plain_bytes = plain_text_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        
        # استخدام دالة bcrypt المدمجة للمقارنة الآمنة
        return bcrypt.checkpw(plain_bytes, hashed_bytes)
    except (ValueError, TypeError):
        # في حال كانت كلمة المرور المخزنة تالفة أو بصيغة غير صحيحة
        return False