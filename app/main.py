import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from dotenv import load_dotenv

# استيراد الوحدات اللازمة من مشروعنا
from app.database.database_setup import setup_database
from app.utils.app_logger import configure_logging, get_logger
from app.database.database_manager import DatabaseManager
from app.login_window_elegant import LoginWindow

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

    # 2. Initialize database
    from app.database.database_setup import setup_database_sync
    setup_database_sync()
    
    # 3. إنشاء نسخة من التطبيق
    app = QApplication(sys.argv)
    
    # 4. تحميل الإعدادات من قاعدة البيانات لتطبيقها عند بدء التشغيل
    # استخدام النظام الهجين إذا كان Enabledاً
    HYBRID_MODE = os.getenv('HYBRID_MODE', 'true').lower() == 'true'
    IS_SUPABASE = bool(os.getenv("NEXT_PUBLIC_SUPABASE_URL") or os.getenv("SUPABASE_URL"))
    
    if HYBRID_MODE and IS_SUPABASE:
        from app.database.simple_hybrid_manager import SimpleHybridManager
        
        db_manager = SimpleHybridManager()
        logger.info("🚀 Using Simple Hybrid Database System - INSTANT MODE")
        logger.info("   📍 All operations are LOCAL for maximum speed")
        logger.info("   ⚡ INSTANT sync with Supabase (immediate + every 5 seconds)")
        logger.info("   🎯 Real-time bi-directional synchronization")
        logger.info("   🚀 Zero latency, instant updates!")
    else:
        db_manager = DatabaseManager()
        logger.info("💾 Using Local Database System")
    
    settings = db_manager.get_all_settings()
    
    # 5. تحميل وتطبيق الثيم الأولي للتطبيق (Stylesheet)
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
    login_win = LoginWindow(db_manager=db_manager)
    login_win.show()
    
    # 7. بدء حلقة أحداث التطبيق، والتي تبقيه قيد التشغيل
    logger.info("Application started. Showing LoginWindow.")
    sys.exit(app.exec())

if __name__ == '__main__':
    # هذا يضمن أن دالة main يتم استدعاؤها فقط عند تشغيل هذا السكربت مباشرة
    main()