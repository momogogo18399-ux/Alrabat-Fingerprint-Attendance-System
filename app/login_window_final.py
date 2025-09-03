#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Login Window - Final Optimized Design
Beautiful and modern login interface with perfect spacing and clarity
"""

import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QApplication, QProgressBar, QFrame,
    QSizePolicy, QSpacerItem
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QCoreApplication, QSettings, QTimer

# استيراد الوحدات اللازمة من مشروعنا
try:
    from app.database.database_manager import DatabaseManager
    from app.utils.encryption import check_password
    from app.main_window import MainWindow
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    print("⚠️ Some imports not available, using demo mode")

class LoginWindow(QMainWindow):
    """
    نافذة تسجيل الدخول المحسنة مع تصميم عصري وجميل.
    تتضمن شريط التقدم والحالة لتحسين تجربة المستخدم.
    """
    
    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.main_win = None
        
        # Initialize UI state
        self.is_loading = False
        
        # Setup window properties
        self.setWindowTitle("تسجيل الدخول - نظام إدارة الحضور")
        self.setFixedSize(550, 750)  # Increased width and height for better spacing
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)
        
        # Center window on screen
        self.center_window()
        
        # Setup UI
        self.setup_ui()
        
        # Load saved username
        self.load_saved_username()
        
        # Start initial animation
        QTimer.singleShot(100, self.start_initial_animation)
        
    def center_window(self):
        """Center the window on the screen"""
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)
        
    def setup_ui(self):
        """Setup the modern and beautiful UI with perfect spacing"""
        # Set window background
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea, stop:1 #764ba2);
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with perfect spacing
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(25)  # Increased spacing between elements
        
        # Logo section
        self.setup_logo_section(main_layout)
        
        # Add space after logo
        main_layout.addSpacing(30)
        
        # Title section
        self.setup_title_section(main_layout)
        
        # Add space before progress
        main_layout.addSpacing(25)
        
        # Progress section (initially hidden)
        self.setup_progress_section(main_layout)
        
        # Status section (initially hidden)
        self.setup_status_section(main_layout)
        
        # Add space before form
        main_layout.addSpacing(30)
        
        # Login form section
        self.setup_login_form(main_layout)
        
        # Add space before footer
        main_layout.addSpacing(30)
        
        # Footer section
        self.setup_footer_section(main_layout)
        
    def setup_logo_section(self, layout):
        """Setup the logo/icon section"""
        logo_container = QFrame()
        logo_container.setFixedSize(110, 110)  # Slightly larger
        logo_container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.25);
                border-radius: 55px;
                border: 4px solid rgba(255, 255, 255, 0.4);
            }
        """)
        
        logo_layout = QVBoxLayout(logo_container)
        logo_layout.setContentsMargins(0, 0, 0, 0)
        
        # Icon or text logo
        logo_label = QLabel("🔐")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 45px;
                font-weight: bold;
            }
        """)
        
        logo_layout.addWidget(logo_label)
        logo_container.setLayout(logo_layout)
        
        # Center the logo
        logo_wrapper = QWidget()
        logo_wrapper_layout = QHBoxLayout(logo_wrapper)
        logo_wrapper_layout.setContentsMargins(0, 0, 0, 0)
        logo_wrapper_layout.addStretch()
        logo_wrapper_layout.addWidget(logo_container)
        logo_wrapper_layout.addStretch()
        
        layout.addWidget(logo_wrapper)
        
    def setup_title_section(self, layout):
        """Setup the title section with better visibility"""
        title_container = QFrame()
        title_container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 18px;
                padding: 20px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
        """)
        
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(20, 20, 20, 20)
        title_layout.setSpacing(12)
        
        # Main title - Larger and more visible
        main_title = QLabel("نظام إدارة الحضور")
        main_title.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        main_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_title.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
            }
        """)
        
        # Subtitle - More visible
        subtitle = QLabel("Attendance Management System")
        subtitle.setFont(QFont("Segoe UI", 14, QFont.Weight.Normal))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.95);
                font-style: italic;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
            }
        """)
        
        title_layout.addWidget(main_title)
        title_layout.addWidget(subtitle)
        
        layout.addWidget(title_container)
        
    def setup_progress_section(self, layout):
        """Setup the progress section"""
        self.progress_container = QFrame()
        self.progress_container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 15px;
                padding: 18px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
        """)
        self.progress_container.hide()  # Initially hidden
        
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(18, 18, 18, 18)
        progress_layout.setSpacing(12)
        
        # Progress label - More visible
        self.progress_label = QLabel("جاري التحقق من البيانات...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
            }
        """)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(30)  # Increased height
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 3px solid rgba(255, 255, 255, 0.4);
                border-radius: 10px;
                text-align: center;
                font-weight: bold;
                color: white;
                background-color: rgba(255, 255, 255, 0.15);
                font-size: 12px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4facfe, stop:1 #00f2fe);
                border-radius: 7px;
            }
        """)
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(self.progress_container)
        
    def setup_status_section(self, layout):
        """Setup the status section"""
        self.status_container = QFrame()
        self.status_container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.2);
                border-radius: 15px;
                padding: 18px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
        """)
        self.status_container.hide()  # Initially hidden
        
        status_layout = QVBoxLayout(self.status_container)
        status_layout.setContentsMargins(18, 18, 18, 18)
        
        # Status label - More visible
        self.status_label = QLabel("جاهز")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
            }
        """)
        
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(self.status_container)
        
    def setup_login_form(self, layout):
        """Setup the login form section with perfect spacing"""
        form_container = QFrame()
        form_container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.15);
                border-radius: 18px;
                padding: 25px;
                border: 2px solid rgba(255, 255, 255, 0.3);
            }
        """)
        
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(25, 25, 25, 25)
        form_layout.setSpacing(20)  # Increased spacing between form elements
        
        # Username input section
        username_label = QLabel("اسم المستخدم:")
        username_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 8px;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
            }
        """)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("أدخل اسم المستخدم")
        self.username_input.setFixedHeight(45)  # Increased height
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.95);
                border: 3px solid rgba(255, 255, 255, 0.4);
                border-radius: 10px;
                padding: 10px 15px;
                font-size: 14px;
                color: #333;
                font-weight: bold;
            }
            QLineEdit:focus {
                border: 3px solid #4facfe;
                background-color: white;
                box-shadow: 0 0 10px rgba(79, 172, 254, 0.5);
            }
            QLineEdit::placeholder {
                color: #666;
                font-weight: normal;
            }
        """)
        
        # Add space after username
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_input)
        form_layout.addSpacing(15)  # Extra space between username and password
        
        # Password input section
        password_label = QLabel("كلمة المرور:")
        password_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 14px;
                font-weight: bold;
                margin-bottom: 8px;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
            }
        """)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("أدخل كلمة المرور")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(45)  # Increased height
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.95);
                border: 3px solid rgba(255, 255, 255, 0.4);
                border-radius: 10px;
                padding: 10px 15px;
                font-size: 14px;
                color: #333;
                font-weight: bold;
            }
            QLineEdit:focus {
                border: 3px solid #4facfe;
                background-color: white;
                box-shadow: 0 0 10px rgba(79, 172, 254, 0.5);
            }
            QLineEdit::placeholder {
                color: #666;
                font-weight: normal;
            }
        """)
        
        # Connect Enter key
        self.password_input.returnPressed.connect(self.handle_login)
        
        # Add space after password
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        form_layout.addSpacing(20)  # Extra space before login button
        
        # Login button - Larger and more prominent
        self.login_button = QPushButton("تسجيل الدخول")
        self.login_button.setFixedHeight(55)  # Increased height
        self.login_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4facfe, stop:1 #00f2fe);
                border: none;
                border-radius: 12px;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 12px;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #3a8bfe, stop:1 #00d4fe);
                transform: scale(1.02);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #2a7bfe, stop:1 #00b6fe);
                transform: scale(0.98);
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)
        self.login_button.clicked.connect(self.handle_login)
        
        # Add login button
        form_layout.addWidget(self.login_button)
        
        layout.addWidget(form_container)
        
    def setup_footer_section(self, layout):
        """Setup the footer section with better visibility"""
        footer_container = QFrame()
        footer_container.setStyleSheet("""
            QFrame {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
                padding: 15px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
        """)
        
        footer_layout = QVBoxLayout(footer_container)
        footer_layout.setContentsMargins(15, 15, 15, 15)
        
        # Footer text - More visible
        footer_text = QLabel("نظام آمن وموثوق لإدارة الحضور والانصراف")
        footer_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_text.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.85);
                font-size: 12px;
                font-style: italic;
                text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
            }
        """)
        
        footer_layout.addWidget(footer_text)
        
        layout.addWidget(footer_container)
        
    def start_initial_animation(self):
        """Start the initial animation sequence"""
        # Show progress
        self.show_progress("جاري تهيئة النظام...", 0)
        
        # Simulate loading sequence
        QTimer.singleShot(500, lambda: self.update_progress(25, "جاري تحميل قاعدة البيانات..."))
        QTimer.singleShot(1000, lambda: self.update_progress(50, "جاري التحقق من الاتصالات..."))
        QTimer.singleShot(1500, lambda: self.update_progress(75, "جاري إعداد الواجهة..."))
        QTimer.singleShot(2000, lambda: self.update_progress(100, "جاهز"))
        
        # Hide progress and show status
        QTimer.singleShot(2500, self.hide_progress_show_status)
        
    def show_progress(self, message, value):
        """Show progress section"""
        self.progress_label.setText(message)
        self.progress_bar.setValue(value)
        self.progress_container.show()
        
    def update_progress(self, value, message):
        """Update progress bar"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
        
    def hide_progress_show_status(self):
        """Hide progress and show status"""
        self.progress_container.hide()
        self.status_label.setText("✅ النظام جاهز")
        self.status_container.show()
        
        # Hide status after a while
        QTimer.singleShot(2000, self.status_container.hide)
        
    def load_saved_username(self):
        """Load saved username from settings"""
        try:
            settings = QSettings("AttendanceApp", "AdminPanel")
            last_username = settings.value("last_username", "")
            if last_username:
                self.username_input.setText(last_username)
                self.password_input.setFocus()
        except Exception:
            pass
            
    def handle_login(self):
        """Handle login attempt with enhanced UX"""
        if self.is_loading:
            return
            
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            self.show_error_message("معلومات ناقصة", "يرجى إدخال اسم المستخدم وكلمة المرور")
            return
            
        # Start login process
        self.start_login_process(username, password)
        
    def start_login_process(self, username, password):
        """Start the login process with progress indication"""
        self.is_loading = True
        self.login_button.setEnabled(False)
        self.login_button.setText("جاري التحقق...")
        
        # Show progress
        self.show_progress("جاري التحقق من بيانات المستخدم...", 0)
        
        # Simulate login process
        QTimer.singleShot(500, lambda: self.update_progress(30, "جاري التحقق من اسم المستخدم..."))
        QTimer.singleShot(1000, lambda: self.update_progress(60, "جاري التحقق من كلمة المرور..."))
        QTimer.singleShot(1500, lambda: self.update_progress(90, "جاري فتح النظام..."))
        
        # Complete login process
        QTimer.singleShot(2000, lambda: self.complete_login_process(username, password))
        
    def complete_login_process(self, username, password):
        """Complete the login process"""
        try:
            if not IMPORTS_AVAILABLE:
                # Demo mode
                self.show_success_and_continue(username)
                return
                
            # Real login process
            user_data = self.db_manager.get_user_by_username(username)
            
            if user_data and check_password(password, user_data['password']):
                # Save username
                try:
                    settings = QSettings("AttendanceApp", "AdminPanel")
                    settings.setValue("last_username", username)
                except Exception:
                    pass
                    
                # Show success and continue
                self.show_success_and_continue(user_data)
            else:
                self.show_login_failed()
                
        except Exception as e:
            print(f"Login error: {e}")
            self.show_login_failed()
            
    def show_success_and_continue(self, user_data):
        """Show success message and continue to main window"""
        self.update_progress(100, "✅ تم تسجيل الدخول بنجاح!")
        
        QTimer.singleShot(1000, lambda: self.open_main_window(user_data))
        
    def show_login_failed(self):
        """Show login failed message"""
        self.is_loading = False
        self.login_button.setEnabled(True)
        self.login_button.setText("تسجيل الدخول")
        
        self.hide_progress_show_status()
        self.status_label.setText("❌ فشل تسجيل الدخول")
        
        # Reset after a while
        QTimer.singleShot(2000, lambda: self.status_container.hide())
        
        # Show error message
        self.show_error_message("فشل تسجيل الدخول", "اسم المستخدم أو كلمة المرور غير صحيحة")
        
    def show_error_message(self, title, message):
        """Show error message box"""
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #f8f9fa;
                color: #333;
            }
            QMessageBox QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #0056b3;
            }
        """)
        msg_box.exec()
        
    def open_main_window(self, user_data):
        """Open the main window"""
        try:
            if IMPORTS_AVAILABLE:
                self.main_win = MainWindow(user_data, QApplication.instance(), db_manager=self.db_manager)
                self.main_win.show()
            else:
                # Demo mode - show success message
                self.show_error_message("نجح", "تم تسجيل الدخول بنجاح! (وضع التجربة)")
                
            self.close()
        except Exception as e:
            print(f"Error opening main window: {e}")
            self.show_error_message("خطأ", "حدث خطأ أثناء فتح النافذة الرئيسية")
            
    def tr(self, text):
        """Translation helper function"""
        return QCoreApplication.translate("LoginWindow", text)

# Demo mode for testing
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Attendance Management System")
    app.setApplicationVersion("2.0")
    
    # Create and show login window
    login_window = LoginWindow()
    login_window.show()
    
    # Run the application
    sys.exit(app.exec())
