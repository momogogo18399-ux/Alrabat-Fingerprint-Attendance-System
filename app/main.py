import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from dotenv import load_dotenv

# استيراد الوحدات اللازمة من مشروعنا
from app.database.database_setup import setup_database
from app.utils.app_logger import configure_logging, get_logger
from app.database.database_manager import DatabaseManager
from app.login_window import LoginWindow

def main():
    """
    نقطة الدخول الرئيسية لتطبيق سطح المكتب.
    يقوم بتهيئة قاعدة البيانات، وتطبيق الإعدادات الأولية،
    ثم يقوم بتشغيل نافذة تسجيل الدخول.
    """
    # 0. تهيئة أنظمة السجلات
    configure_logging()
    logger = get_logger("Main")

    # 1. تحميل المتغيرات من ملف .env (يسهّل ضبط DATABASE_URL على أجهزة العملاء)
    try:
        load_dotenv()
    except Exception:
        pass

    # 2. التأكد من إنشاء قاعدة البيانات وجداولها محليًا
    # إذا كان ملف attendance.db غير موجود، سيتم إنشاؤه بالكامل
    setup_database()
    
    # 3. إنشاء نسخة من التطبيق
    app = QApplication(sys.argv)
    
    # 4. تحميل الإعدادات من قاعدة البيانات لتطبيقها عند بدء التشغيل
    db_manager = DatabaseManager()
    settings = db_manager.get_all_settings()
    
    # 5. تحميل وتطبيق الثيم الأولي للتطبيق (Stylesheet)
    import os
    from app.utils.resources import resource_path
    theme_dir = os.getenv('THEME_DIR', resource_path('assets/themes'))
    theme = settings.get('theme', 'light') # استخدام الثيم الفاتح كافتراضي
    try:
        # تأكد من أن المسار صحيح بالنسبة لمكان تشغيل main.py
        with open(os.path.join(theme_dir, f'{theme}.qss'), 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
            print(f"Successfully loaded initial theme: '{theme}.qss' from '{theme_dir}'")
    except FileNotFoundError:
        logger.warning(f"Theme file 'assets/themes/{theme}.qss' not found. Using default application style.")
    except Exception as e:
        logger.error(f"An error occurred while loading the theme file: {e}")

    # ملاحظة: منطق تحميل اللغة وتحديد اتجاه الواجهة موجود الآن في MainWindow
    # للسماح بالتغيير الفوري والديناميكي بعد تسجيل الدخول.

    # 6. إنشاء وعرض نافذة تسجيل الدخول، وهي بوابة الدخول للنظام
    login_win = LoginWindow()
    login_win.show()
    
    # 7. بدء حلقة أحداث التطبيق، والتي تبقيه قيد التشغيل
    logger.info("Application started. Showing LoginWindow.")
    sys.exit(app.exec())

if __name__ == '__main__':
    # هذا يضمن أن دالة main يتم استدعاؤها فقط عند تشغيل هذا السكربت مباشرة
    main()