from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QApplication
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QCoreApplication, QSettings

# استيراد الوحدات اللازمة من مشروعنا
from app.database.database_manager import DatabaseManager
from app.utils.encryption import check_password
from app.main_window import MainWindow

class LoginWindow(QMainWindow):
    """
    نافذة تسجيل الدخول الرئيسية للتطبيق.
    تقوم بالتحقق من هوية المستخدمين قبل منحهم الوصول إلى لوحة التحكم.
    """
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.main_win = None  # للاحتفاظ بمرجع للنافذة الرئيسية

        self.setWindowTitle(self.tr("Login - Attendance Management System"))
        self.setFixedSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        """تنشئ وتنظم عناصر واجهة المستخدم للنافذة."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        
        title_label = QLabel(self.tr("Attendance Management System"))
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText(self.tr("Username"))
        self.username_input.setFixedHeight(35)
        layout.addWidget(self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(self.tr("Password"))
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password) # لإخفاء كلمة المرور
        self.password_input.setFixedHeight(35)
        # السماح بتسجيل الدخول عند الضغط على Enter في حقل كلمة المرور
        self.password_input.returnPressed.connect(self.handle_login)
        layout.addWidget(self.password_input)

        login_button = QPushButton(self.tr("Login"))
        login_button.setFixedHeight(40)
        login_button.clicked.connect(self.handle_login)
        layout.addWidget(login_button)

        # تذكّر آخر اسم مستخدم
        try:
            settings = QSettings("AttendanceApp", "AdminPanel")
            last_username = settings.value("last_username", "")
            if last_username:
                self.username_input.setText(last_username)
        except Exception:
            pass

    def handle_login(self):
        """تعالج محاولة تسجيل دخول المستخدم."""
        username = self.username_input.text().strip()
        password = self.password_input.text()

        if not username or not password:
            QMessageBox.warning(
                self, 
                self.tr("Missing Information"), 
                self.tr("Please enter both username and password.")
            )
            return

        user_data = self.db_manager.get_user_by_username(username)

        # التحقق من وجود المستخدم وصحة كلمة المرور
        if user_data and check_password(password, user_data['password']):
            # حفظ آخر اسم مستخدم ناجح
            try:
                settings = QSettings("AttendanceApp", "AdminPanel")
                settings.setValue("last_username", username)
            except Exception:
                pass
            # عند النجاح، افتح النافذة الرئيسية وأغلق نافذة تسجيل الدخول
            # نمرر نسخة التطبيق (app instance) للسماح بالتحكم في الثيم واللغة
            self.main_win = MainWindow(user_data, QApplication.instance())
            self.main_win.show()
            self.close()
        else:
            QMessageBox.critical(
                self, 
                self.tr("Login Failed"), 
                self.tr("Invalid username or password. Please try again.")
            )
    
    def tr(self, text):
        """دالة مساعدة للترجمة."""
        return QCoreApplication.translate("LoginWindow", text)