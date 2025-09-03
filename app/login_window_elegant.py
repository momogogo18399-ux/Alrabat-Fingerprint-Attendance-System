#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Login Window - Elegant Simple Modern Design
Clean, simple and modern login interface
"""

import sys
import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QApplication, QProgressBar, QFrame, QStackedWidget
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QCoreApplication, QSettings, QTimer

# Import required modules from our project
try:
    from app.database.database_manager import DatabaseManager
    from app.utils.encryption import check_password
    from app.main_window import MainWindow
    IMPORTS_AVAILABLE = True
except ImportError:
    IMPORTS_AVAILABLE = False
    print("⚠️ Some imports not available, using demo mode")

class ElegantFrame(QFrame):
    """Simple elegant frame with subtle styling"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            ElegantFrame {
                background-color: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 16px;
            }
        """)

class LoginWindow(QMainWindow):
    """
    Login Window with elegant, simple and modern design.
    Calm colors and clean layout.
    """
    
    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager
        self.main_win = None
        
        # Initialize UI state
        self.is_loading = False
        
        # Setup window properties
        self.setWindowTitle("Login - Attendance Management System")
        self.setFixedSize(500, 750)  # Increased size for better spacing
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
        """Setup the elegant and simple UI design"""
        # Set window background with elegant gradient
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #f8fafc, stop:0.5 #e2e8f0, stop:1 #cbd5e1);
            }
        """)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(25)
        
        # Header section
        self.setup_header_section(main_layout)
        
        # Create stacked widget for progress/status and form
        self.stacked_widget = QStackedWidget()
        self.setup_stacked_widget()
        main_layout.addWidget(self.stacked_widget)
        
        # Footer section
        self.setup_footer_section(main_layout)
        
    def setup_stacked_widget(self):
        """Setup stacked widget to prevent overlap"""
        # Page 0: Login Form
        self.form_page = QWidget()
        self.setup_login_form_page()
        self.stacked_widget.addWidget(self.form_page)
        
        # Page 1: Progress
        self.progress_page = QWidget()
        self.setup_progress_page()
        self.stacked_widget.addWidget(self.progress_page)
        
        # Page 2: Status
        self.status_page = QWidget()
        self.setup_status_page()
        self.stacked_widget.addWidget(self.status_page)
        
        # Start with form page
        self.stacked_widget.setCurrentIndex(0)
        
    def setup_header_section(self, layout):
        """Setup the elegant header section"""
        header_container = ElegantFrame()
        header_layout = QVBoxLayout(header_container)
        header_layout.setContentsMargins(32, 32, 32, 32)
        header_layout.setSpacing(16)
        
        # Icon section
        icon_label = QLabel("✨")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("""
            QLabel {
                color: #6366f1;
                font-size: 48px;
                font-weight: normal;
            }
        """)
        
        # Main title
        main_title = QLabel("Welcome")
        main_title.setFont(QFont("Segoe UI", 24, QFont.Weight.Medium))
        main_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_title.setStyleSheet("""
            QLabel {
                color: #1e293b;
                font-weight: 500;
            }
        """)
        
        # Subtitle
        subtitle = QLabel("Sign in to access the system")
        subtitle.setFont(QFont("Segoe UI", 14, QFont.Weight.Normal))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("""
            QLabel {
                color: #64748b;
                font-weight: normal;
            }
        """)
        
        header_layout.addWidget(icon_label)
        header_layout.addWidget(main_title)
        header_layout.addWidget(subtitle)
        
        layout.addWidget(header_container)
        
    def setup_login_form_page(self):
        """Setup the login form page"""
        form_layout = QVBoxLayout(self.form_page)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(0)
        
        # Form container
        form_container = ElegantFrame()
        form_layout.addWidget(form_container)
        
        # Form content
        form_content = QVBoxLayout(form_container)
        form_content.setContentsMargins(40, 40, 40, 40)
        form_content.setSpacing(20)
        
        # Username input section
        username_label = QLabel("Username")
        username_label.setStyleSheet("""
            QLabel {
                color: #374151;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setFixedHeight(44)
        self.username_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 0px 16px;
                font-size: 14px;
                color: #1f2937;
                font-weight: normal;
            }
            QLineEdit:focus {
                border: 2px solid #6366f1;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #9ca3af;
                font-weight: normal;
            }
        """)
        
        # Password input section
        password_label = QLabel("Password")
        password_label.setStyleSheet("""
            QLabel {
                color: #374151;
                font-size: 14px;
                font-weight: 500;
            }
        """)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(44)
        self.password_input.setStyleSheet("""
            QLineEdit {
                background-color: white;
                border: 1px solid #d1d5db;
                border-radius: 8px;
                padding: 0px 16px;
                font-size: 14px;
                color: #1f2937;
                font-weight: normal;
            }
            QLineEdit:focus {
                border: 2px solid #6366f1;
                background-color: white;
            }
            QLineEdit::placeholder {
                color: #9ca3af;
                font-weight: normal;
            }
        """)
        
        # Connect Enter key
        self.password_input.returnPressed.connect(self.handle_login)
        
        # Login button with elegant design
        self.login_button = QPushButton("Sign In")
        self.login_button.setFixedHeight(48)
        self.login_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                border: none;
                border-radius: 8px;
                color: white;
                font-size: 15px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #5855eb, stop:1 #7c3aed);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #4f46e5, stop:1 #6d28d9);
            }
            QPushButton:disabled {
                background-color: #d1d5db;
                color: #6b7280;
            }
        """)
        self.login_button.clicked.connect(self.handle_login)
        
        # Add form elements
        form_content.addWidget(username_label)
        form_content.addWidget(self.username_input)
        form_content.addWidget(password_label)
        form_content.addWidget(self.password_input)
        form_content.addSpacing(10)
        form_content.addWidget(self.login_button)
        
    def setup_progress_page(self):
        """Setup the progress page"""
        progress_layout = QVBoxLayout(self.progress_page)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        progress_layout.setSpacing(0)
        
        # Progress container
        progress_container = ElegantFrame()
        progress_layout.addWidget(progress_container)
        
        # Progress content
        progress_content = QVBoxLayout(progress_container)
        progress_content.setContentsMargins(40, 40, 40, 40)
        progress_content.setSpacing(20)
        
        # Progress label
        self.progress_label = QLabel("Verifying data...")
        self.progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_label.setStyleSheet("""
            QLabel {
                color: #6366f1;
                font-size: 16px;
                font-weight: 500;
            }
        """)
        
        # Progress bar with elegant design
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 6px;
                background-color: #e2e8f0;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #8b5cf6);
                border-radius: 6px;
            }
        """)
        
        progress_content.addWidget(self.progress_label)
        progress_content.addWidget(self.progress_bar)
        
    def setup_status_page(self):
        """Setup the status page"""
        status_layout = QVBoxLayout(self.status_page)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(0)
        
        # Status container
        status_container = ElegantFrame()
        status_layout.addWidget(status_container)
        
        # Status content
        status_content = QVBoxLayout(status_container)
        status_content.setContentsMargins(40, 40, 40, 40)
        status_content.setSpacing(20)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                color: #10b981;
                font-size: 16px;
                font-weight: 500;
            }
        """)
        
        status_content.addWidget(self.status_label)
        
    def setup_footer_section(self, layout):
        """Setup the footer section with elegant design"""
        footer_container = ElegantFrame()
        footer_layout = QVBoxLayout(footer_container)
        footer_layout.setContentsMargins(24, 24, 24, 24)
        
        # Footer text
        footer_text = QLabel("Attendance Management System")
        footer_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer_text.setStyleSheet("""
            QLabel {
                color: #6b7280;
                font-size: 13px;
                font-weight: normal;
            }
        """)
        
        footer_layout.addWidget(footer_text)
        
        layout.addWidget(footer_container)
        
    def start_initial_animation(self):
        """Start the initial animation sequence"""
        # Show progress
        self.show_progress("Initializing system...", 0)
        
        # Simulate loading sequence
        QTimer.singleShot(500, lambda: self.update_progress(25, "Loading database..."))
        QTimer.singleShot(1000, lambda: self.update_progress(50, "Checking connections..."))
        QTimer.singleShot(1500, lambda: self.update_progress(75, "Setting up interface..."))
        QTimer.singleShot(2000, lambda: self.update_progress(100, "Ready"))
        
        # Hide progress and show status
        QTimer.singleShot(2500, self.hide_progress_show_status)
        
    def show_progress(self, message, value):
        """Show progress page"""
        self.progress_label.setText(message)
        self.progress_bar.setValue(value)
        self.stacked_widget.setCurrentIndex(1)  # Switch to progress page
        
    def update_progress(self, value, message):
        """Update progress bar"""
        self.progress_bar.setValue(value)
        self.progress_label.setText(message)
        
    def hide_progress_show_status(self):
        """Hide progress and show status"""
        self.status_label.setText("✅ System Ready")
        self.stacked_widget.setCurrentIndex(2)  # Switch to status page
        
        # Hide status after a while and return to form
        QTimer.singleShot(2000, self.return_to_form)
        
    def return_to_form(self):
        """Return to login form"""
        self.stacked_widget.setCurrentIndex(0)  # Switch back to form page
        
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
            self.show_error_message("Missing Information", "Please enter username and password")
            return
            
        # Start login process
        self.start_login_process(username, password)
        
    def start_login_process(self, username, password):
        """Start the login process with progress indication"""
        self.is_loading = True
        self.login_button.setEnabled(False)
        self.login_button.setText("Verifying...")
        
        # Show progress
        self.show_progress("Verifying user data...", 0)
        
        # Simulate login process
        QTimer.singleShot(500, lambda: self.update_progress(30, "Checking username..."))
        QTimer.singleShot(1000, lambda: self.update_progress(60, "Verifying password..."))
        QTimer.singleShot(1500, lambda: self.update_progress(90, "Opening system..."))
        
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
        self.update_progress(100, "✅ Login successful!")
        
        QTimer.singleShot(1000, lambda: self.open_main_window(user_data))
        
    def show_login_failed(self):
        """Show login failed message"""
        self.is_loading = False
        self.login_button.setEnabled(True)
        self.login_button.setText("Sign In")
        
        # Show status and return to form
        self.status_label.setText("❌ Login failed")
        self.stacked_widget.setCurrentIndex(2)  # Show status page
        
        # Return to form after a while
        QTimer.singleShot(2000, self.return_to_form)
        
        # Show error message
        self.show_error_message("Login Failed", "Username or password is incorrect")
        
    def show_error_message(self, title, message):
        """Show error message box"""
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setStyleSheet("""
            QMessageBox {
                background-color: #f8fafc;
                color: #1f2937;
            }
            QMessageBox QPushButton {
                background-color: #6366f1;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
            }
            QMessageBox QPushButton:hover {
                background-color: #5855eb;
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
                self.show_error_message("Success", "Login successful! (Demo mode)")
                
            self.close()
        except Exception as e:
            print(f"Error opening main window: {e}")
            self.show_error_message("Error", "An error occurred while opening the main window")
            
    def tr(self, text):
        """Translation helper function"""
        return QCoreApplication.translate("LoginWindow", text)

# Demo mode for testing
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Attendance Management System")
    app.setApplicationVersion("4.0")
    
    # Create and show login window
    login_window = LoginWindow()
    login_window.show()
    
    # Run the application
    sys.exit(app.exec())
