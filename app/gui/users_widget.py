from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import QCoreApplication
from app.database.database_manager import DatabaseManager
from app.utils.encryption import hash_password
from app.gui.user_dialog import UserDialog
from app.gui.password_dialog import PasswordDialog

class UsersWidget(QWidget):
    """واجهة متكاملة لإدارة مستخدمي البرنامج."""
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.setup_ui()
        self.connect_signals()
        self.load_users_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        button_layout = QHBoxLayout()
        self.add_user_button = QPushButton(f"➕ {self.tr('Add User')}")
        self.edit_user_button = QPushButton(f"✏️ {self.tr('Edit Role')}")
        self.change_pass_button = QPushButton(f"🔑 {self.tr('Change Password')}")
        self.delete_user_button = QPushButton(f"🗑️ {self.tr('Delete User')}")
        
        button_layout.addWidget(self.add_user_button)
        button_layout.addWidget(self.edit_user_button)
        button_layout.addWidget(self.change_pass_button)
        button_layout.addWidget(self.delete_user_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ID", self.tr("Username"), self.tr("Role")])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

    def connect_signals(self):
        self.add_user_button.clicked.connect(self.add_user)
        self.edit_user_button.clicked.connect(self.edit_user)
        self.change_pass_button.clicked.connect(self.change_password)
        self.delete_user_button.clicked.connect(self.delete_user)

    def load_users_data(self):
        users = self.db_manager.get_all_users()
        self.table.setRowCount(0)
        self.table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(user['username']))
            self.table.setItem(row, 2, QTableWidgetItem(user['role']))

    def add_user(self):
        dialog = UserDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                hashed_pass = hash_password(data['password'])
                if self.db_manager.add_user(data['username'], hashed_pass, data['role']):
                    QMessageBox.information(self, self.tr("Success"), self.tr("User added successfully."))
                    self.load_users_data()
                else:
                    QMessageBox.critical(self, self.tr("Error"), self.tr("Username might already exist."))

    def edit_user(self):
        selected_row = self.table.currentRow()
        if selected_row < 0: return
        user_id = int(self.table.item(selected_row, 0).text())
        if user_id == 1:
            QMessageBox.warning(self, self.tr("Action Not Allowed"), self.tr("The main admin's role cannot be changed."))
            return
        
        user_data = {'id': user_id, 'username': self.table.item(selected_row, 1).text(), 'role': self.table.item(selected_row, 2).text()}
        dialog = UserDialog(user_data=user_data, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                if self.db_manager.update_user_role(data['id'], data['role']):
                    QMessageBox.information(self, self.tr("Success"), self.tr("User role updated successfully."))
                    self.load_users_data()

    def change_password(self):
        selected_row = self.table.currentRow()
        if selected_row < 0: return
        user_id = int(self.table.item(selected_row, 0).text())
        username = self.table.item(selected_row, 1).text()
        
        dialog = PasswordDialog(username, self)
        if dialog.exec():
            password = dialog.get_password()
            if password:
                hashed_pass = hash_password(password)
                if self.db_manager.update_user_password(user_id, hashed_pass):
                    QMessageBox.information(self, self.tr("Success"), self.tr("Password updated successfully."))

    def delete_user(self):
        selected_row = self.table.currentRow()
        if selected_row < 0: return
        user_id = int(self.table.item(selected_row, 0).text())
        username = self.table.item(selected_row, 1).text()
        
        if user_id == 1:
            QMessageBox.critical(self, self.tr("Action Not Allowed"), self.tr("The main admin account cannot be deleted."))
            return
        
        reply = QMessageBox.question(self, self.tr("Confirm Deletion"), f"{self.tr('Delete user')} {username}?")
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_user(user_id):
                QMessageBox.information(self, self.tr("Success"), self.tr("User deleted successfully."))
                self.load_users_data()

    def tr(self, text):
        return QCoreApplication.translate("UsersWidget", text)