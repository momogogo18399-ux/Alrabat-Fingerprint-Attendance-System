from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QApplication
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QCoreApplication
from app.database.database_manager import DatabaseManager
from app.utils.encryption import check_password
from app.main_window import MainWindow

class LoginWindow(QMainWindow):
    """
    The main login window for the application.
    Authenticates users before granting access to the main dashboard.
    """
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.main_win = None  # To hold a reference to the main window

        self.setWindowTitle(self.tr("Login - Attendance Management System"))
        self.setFixedSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        """Creates and arranges the UI elements for the window."""
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
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setFixedHeight(35)
        # Allow login by pressing Enter in the password field
        self.password_input.returnPressed.connect(self.handle_login)
        layout.addWidget(self.password_input)

        login_button = QPushButton(self.tr("Login"))
        login_button.setFixedHeight(40)
        # The stylesheet is now handled globally by main.py, so we remove the line below
        # login_button.setStyleSheet("...") 
        login_button.clicked.connect(self.handle_login)
        layout.addWidget(login_button)

    def handle_login(self):
        """Handles the user login attempt."""
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

        # Check if user exists and password is correct
        if user_data and check_password(password, user_data['password']):
            # On successful login, open the main window and close this one
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
        """Helper function for translation."""
        return QCoreApplication.translate("LoginWindow", text)