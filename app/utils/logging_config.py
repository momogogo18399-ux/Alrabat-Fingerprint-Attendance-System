import logging
import os
from datetime import datetime

def setup_logging():
    """إعداد نظام التسجيل الآمن"""
    # إنشاء مجلد السجلات
    log_dir = "logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # إعداد التسجيل
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'{log_dir}/app_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler()
        ]
    )
    
    # إخفاء رسائل الحزم الخارجية
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

def get_logger(name):
    """الحصول على logger آمن"""
    return logging.getLogger(name)

def log_error(error, context=None, sensitive_data=None):
    """تسجيل الأخطاء بشكل آمن"""
    logger = get_logger('error')
    message = f"Error in {context}: {str(error)}"
    
    if sensitive_data:
        # تشفير البيانات الحساسة
        message = message.replace(sensitive_data, "[REDACTED]")
    
    logger.error(message)
