import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from app.database.database_setup import setup_database
from app.database.database_manager import DatabaseManager
from app.login_window import LoginWindow

def main():
    """
    نقطة الدخول الرئيسية لتطبيق سطح المكتب.
    يقوم بتهيئة قاعدة البيانات، وتطبيق الإعدادات الأولية (الثيم)،
    ثم يقوم بتشغيل نافذة تسجيل الدخول.
    """
    # 1. التأكد من إنشاء قاعدة البيانات وجداولها
    setup_database()
    
    # 2. إنشاء نسخة من التطبيق
    app = QApplication(sys.argv)
    
    # 3. تحميل الإعدادات من قاعدة البيانات
    db_manager = DatabaseManager()
    settings = db_manager.get_all_settings()
    
    # 4. تحميل وتطبيق الثيم الأولي للتطبيق (Stylesheet)
    theme = settings.get('theme', 'light') # استخدام الثيم الفاتح كافتراضي
    try:
        with open(f'assets/themes/{theme}.qss', 'r', encoding='utf-8') as f:
            app.setStyleSheet(f.read())
            print(f"Successfully loaded initial theme: '{theme}.qss'")
    except FileNotFoundError:
        print(f"Theme file '{theme}.qss' not found. Using default application style.")
    except Exception as e:
        print(f"An error occurred while loading the theme file: {e}")

    # ملاحظة: تم نقل منطق تحميل اللغة وتحديد اتجاه الواجهة إلى MainWindow
    # للسماح بالتغيير الفوري والديناميكي بعد تسجيل الدخول.

    # 5. إنشاء وعرض نافذة تسجيل الدخول
    login_win = LoginWindow()
    login_win.show()
    
    # 6. بدء حلقة أحداث التطبيق
    sys.exit(app.exec())

if __name__ == '__main__':
    # هذا يضمن أن دالة main يتم استدعاؤها فقط عند تشغيل السكربت مباشرة
    main()