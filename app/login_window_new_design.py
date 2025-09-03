#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Login Window - New Modern Design
Fresh and attractive login interface with new colors and layout
"""

import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QApplication, QProgressBar, QFrame,
    QSizePolicy, QSpacerItem
)
from PyQt6.QtGui import QFont, QPixmap, QPainter, QColor, QLinearGradient
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

class ModernFrame(QFrame):
    """Custom frame with modern styling"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            ModernFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba(255, 255, 255, 0.1),
                    stop:1 rgba(255, 255, 255, 0.05));
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 20px;
                backdrop-filter: blur(10px);
            }
        """)

class LoginWindow(QMainWindow):
    """
    نافذة تسجيل الدخول بتصميم جديد وعصري.
    ألوان وتخطيط مختلف تماماً.
    """
    
    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.main_win = None
        
        # Initialize UI state
        self.is_loading = False
        
        # Setup window properties
        self.setWindowTitle("تسجيل الدخول - نظام إدارة الحضور")
        self.setFixedSize(600, 800)
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowCloseButtonHint)
        
        # Remove window frame for modern look
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
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
        """Setup the new modern UI design"""
        # Set window background with new gradient
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a2e, stop:0.3 #16213e, stop:0.7 #0f3460, stop:1 #533483);
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(50, 50, 50, 50)
        main_layout.setSpacing(30)
        
        # Close button at top right
        self.setup_close_button(main_layout)
        
        # Header section
        self.setup_header_section(main_layout)
        
        # Progress section (initially hidden)
        self.setup_progress_section(main_layout)
        
        # Status section (initially hidden)
        self.setup_status_section(main_layout)
        
        # Login form section
        self.setup_login_form(main_layout)
        
        # Footer section
        self.setup_footer_section(main_layout)
        
    def setup_close_button(self, layout):
        """Setup close button at top right"""
        close_container = QWidget()
        close_layout = QHBoxLayout(close_container)
        close_layout.setContentsMargins(0, 0, 0, 0)
        
        # Spacer to push button to right
        close_layout.addStretch()
        
        # Close button
        close_button = QPushButton("✕")
        close_button.setFixedSize(40, 40)
        close_button.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(255, 255, 255, 0.2);
                border-radius: 20px;
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
                border: 2px solid rgba(255, 255, 255, 0.4);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        close_button.clicked.connect(self.close)
        
        close_layout.addWidget(close_button)
        layout.addWidget(close_container)
        
    def setup_header_section(self, layout):
        """Setup the header section with new design"""
        header_container = ModernFrame()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(30, 30, 30, 30)
        header_layout.setSpacing(20)
        
        # Icon section
        icon_label = QLabel("🎯")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                color: #00d4ff;
                font-size: 60px;
                font-weight: bold;
                text-shadow: 0 0 20px rgba(0, 212, 255, 0.5);
            }
        """)
        
        # Main title
        main_title = QLabel("مرحباً بك")
        main_title.setFont(QFont("Segoe UI", 28, QFont.Weight.Bold))
        main_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_title.setStyleSheet("""
            QLabel {
                color: white;
                font-weight: bold;
                text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
            }
        """)
        
        # Subtitle
        subtitle = QLabel("سجل دخولك للوصول للنظام")
        subtitle.setFont(QFont("Segoe UI", 16, QFont.Weight.Normal))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                color: #00d4ff;
                font-style: italic;
                text-shadow: 0 0 8px rgba(0, 212, 255, 0.3);
            }
        """)
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(main_title)
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header_container)
        
    def setup_progress_section(self, layout):
        """Setup the progress section with new design"""
        self.progress_container = ModernFrame()
        self.progress_container.hide()  # Initially hidden
        
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(25, 25, 25, 25)
        progress_layout.setSpacing(15)
        
        # Progress label
        self.progress_label = QLabel("جاري التحقق من البيانات...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #00d4ff;
                font-size: 16px;
                font-weight: bold;
                text-shadow: 0 0 8px rgba(0, 212, 255, 0.3);
            }
        """)
        
        # Progress bar with new design
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(35)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 3px solid rgba(0, 212, 255, 0.3);
                border-radius: 15px;
                text-align: center;
                font-weight: bold;
                color: white;
                background-color: rgba(0, 212, 255, 0.1);
                font-size: 14px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4ff, stop:1 #0099cc);
                border-radius: 12px;
            }
        """)
        
        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(self.progress_container)
        
    def setup_status_section(self, layout):
        """Setup the status section with new design"""
        self.status_container = ModernFrame()
        self.status_container.hide()  # Initially hidden
        
        status_layout = QVBoxLayout(self.status_container)
        status_layout.setContentsMargins(25, 25, 25, 25)
        
        # Status label
        self.status_label = QLabel("جاهز")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #00ff88;
                font-size: 16px;
                font-weight: bold;
                text-shadow: 0 0 8px rgba(0, 255, 136, 0.3);
            }
        """)
        
        status_layout.addWidget(self.status_label)
        
        layout.addWidget(self.status_container)
        
    def setup_login_form(self, layout):
        """Setup the login form section with new design"""
        form_container = ModernFrame()
        form_layout = QVBoxLayout(form_container)
        form_layout.setContentsMargins(35, 35, 35, 35)
        form_layout.setSpacing(25)
        
        # Username input section
        username_label = QLabel("اسم المستخدم")
        username_label.setStyleSheet("""
            QLabel {
                color: #00d4ff;
                font-size: 16px;
                font-weight: bold;
                text-shadow: 0 0 8px rgba(0, 212, 255, 0.3);
            }
        """)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("أدخل اسم المستخدم هنا")
        self.username_input.setFixedHeight(50)
        self.username_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(0, 212, 255, 0.3);
                border-radius: 15px;
                padding: 0px 20px;
                font-size: 16px;
                color: white;
                font-weight: bold;
            }
            QLineEdit:focus {
                border: 2px solid #00d4ff;
                background: rgba(255, 255, 255, 0.15);
                box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.5);
                font-weight: normal;
            }
        """)
        
        # Password input section
        password_label = QLabel("كلمة المرور")
        password_label.setStyleSheet("""
            QLabel {
                color: #00d4ff;
                font-size: 16px;
                font-weight: bold;
                text-shadow: 0 0 8px rgba(0, 212, 255, 0.3);
            }
        """)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("أدخل كلمة المرور هنا")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(50)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.1);
                border: 2px solid rgba(0, 212, 255, 0.3);
                border-radius: 15px;
                padding: 0px 20px;
                font-size: 16px;
                color: white;
                font-weight: bold;
            }
            QLineEdit:focus {
                border: 2px solid #00d4ff;
                background: rgba(255, 255, 255, 0.15);
                box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
            }
            QLineEdit::placeholder {
                color: rgba(255, 255, 255, 0.5);
                font-weight: normal;
            }
        """)
        
        # Connect Enter key
        self.password_input.returnPressed.connect(self.handle_login)
        
        # Login button with new design
        self.login_button = QPushButton("دخول")
        self.login_button.setFixedHeight(55)
        self.login_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00d4ff, stop:1 #0099cc);
                border: none;
                border-radius: 20px;
                color: white;
                font-size: 18px;
                font-weight: bold;
                text-shadow: 0 0 10px rgba(255, 255, 255, 0.3);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00e6ff, stop:1 #00aadd);
                box-shadow: 0 0 25px rgba(0, 212, 255, 0.4);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00b3e6, stop:1 #0088bb);
            }
            QPushButton:disabled {
                background: rgba(128, 128, 128, 0.5);
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        self.login_button.clicked.connect(self.handle_login)
        
        # Add form elements
        form_layout.addWidget(username_label)
        form_layout.addWidget(self.username_input)
        form_layout.addWidget(password_label)
        form_layout.addWidget(self.password_input)
        form_layout.addSpacing(10)
        form_layout.addWidget(self.login_button)
        
        layout.addWidget(form_container)
        
    def setup_footer_section(self, layout):
        """Setup the footer section with new design"""
        footer_container = ModernFrame()
        footer_layout = QVBoxLayout(footer_container)
        footer_layout.setContentsMargins(25, 25, 25, 25)
        
        # Footer text
        footer_text = QLabel("نظام إدارة الحضور المتطور")
        footer_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_text.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.6);
                font-size: 14px;
                font-style: italic;
                text-shadow: 0 0 5px rgba(255, 255, 255, 0.2);
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
        self.login_button.setText("دخول")
        
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
                background-color: #1a1a2e;
                color: white;
            }
            QMessageBox QPushButton {
                background-color: #00d4ff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 10px;
                font-weight: bold;
            }
            QMessageBox QPushButton:hover {
                background-color: #00e6ff;
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
    app.setApplicationVersion("3.0")
    
    # Create and show login window
    login_window = LoginWindow()
    login_window.show()
    
    # Run the application
    sys.exit(app.exec())
