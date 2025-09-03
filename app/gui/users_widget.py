from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView
)
from PyQt6.QtCore import QCoreApplication

# استيراد الوحدات اللازمة
from app.database.simple_hybrid_manager import SimpleHybridManager
from app.utils.encryption import hash_password
from app.gui.user_dialog import UserDialog
from app.gui.password_dialog import PasswordDialog

class UsersWidget(QWidget):
    """
    Integrated interface for managing program users (المديرين والمشرفين).
    """
    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager or SimpleHybridManager()
        self.setup_ui()
        self.connect_signals()
        self.load_users_data()

    def setup_ui(self):
        """تنشئ وتنظم عناصر الواجهة."""
        layout = QVBoxLayout(self)
        button_layout = QHBoxLayout()
        self.add_user_button = QPushButton(f"➕ {self.tr('Add User')}")
        self.add_user_button.setToolTip(self.tr("Create a new application user"))
        self.edit_user_button = QPushButton(f"✏️ {self.tr('Edit Role')}")
        self.edit_user_button.setToolTip(self.tr("Change the selected user's role"))
        self.change_pass_button = QPushButton(f"🔑 {self.tr('Change Password')}")
        self.change_pass_button.setToolTip(self.tr("Set a new password for the selected user"))
        self.delete_user_button = QPushButton(f"🗑️ {self.tr('Delete User')}")
        self.delete_user_button.setToolTip(self.tr("Delete the selected user (except main admin)"))
        
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
        self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

    def connect_signals(self):
        """تربط إشارات الأزرار بالدوال الخاصة بها."""
        self.add_user_button.clicked.connect(self.add_user)
        self.edit_user_button.clicked.connect(self.edit_user)
        self.change_pass_button.clicked.connect(self.change_password)
        self.delete_user_button.clicked.connect(self.delete_user)

    def load_users_data(self):
        """تحمل بيانات المستخدمين من قاعدة البيانات وتملأ الجدول."""
        users = self.db_manager.get_all_users() or []
        self.table.setRowCount(0)
        self.table.setRowCount(len(users))
        for row, user in enumerate(users):
            self.table.setItem(row, 0, QTableWidgetItem(str(user['id'])))
            self.table.setItem(row, 1, QTableWidgetItem(user['username']))
            self.table.setItem(row, 2, QTableWidgetItem(user['role']))

    def add_user(self):
        """تفتح نافذة لAdd مستخدم جديد."""
        dialog = UserDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                hashed_pass = hash_password(data['password'])
                user_data = {
                    'username': data['username'],
                    'password': hashed_pass,
                    'role': data['role']
                }
                result = self.db_manager.add_user(user_data)
                if result is not None:
                    QMessageBox.information(self, self.tr("Success"), self.tr("User added successfully."))
                    self.load_users_data()
                else:
                    QMessageBox.critical(self, self.tr("Error"), self.tr("Username might already exist."))

    def edit_user(self):
        """تفتح نافذة لEdit دور المستخدم المحدد."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select a user to edit.")); return
        
        user_id = int(self.table.item(selected_row, 0).text())
        if user_id == 1:
            QMessageBox.warning(self, self.tr("Action Not Allowed"), self.tr("The main admin's role cannot be changed."))
            return
        
        user_data = {'id': user_id, 'username': self.table.item(selected_row, 1).text(), 'role': self.table.item(selected_row, 2).text()}
        dialog = UserDialog(user_data=user_data, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                # Update دور المستخدم باستخدام update_user
                update_data = {'role': data['role']}
                if self.db_manager.update_user(data['id'], update_data):
                    QMessageBox.information(self, self.tr("Success"), self.tr("User role updated successfully."))
                    self.load_users_data()
                else:
                    QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to update user role."))

    def change_password(self):
        """تفتح نافذة لتغيير كلمة مرور المستخدم المحدد."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select a user to change their password.")); return
            
        user_id = int(self.table.item(selected_row, 0).text())
        username = self.table.item(selected_row, 1).text()
        
        dialog = PasswordDialog(username, self)
        if dialog.exec():
            password = dialog.get_password()
            if password:
                hashed_pass = hash_password(password)
                # Update كلمة المرور باستخدام update_user
                update_data = {'password': hashed_pass}
                if self.db_manager.update_user(user_id, update_data):
                    QMessageBox.information(self, self.tr("Success"), self.tr("Password updated successfully."))
                else:
                    QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to update password."))

    def delete_user(self):
        """تDelete المستخدم المحدد بعد الConfirm."""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select a user to delete.")); return
            
        user_id = int(self.table.item(selected_row, 0).text())
        username = self.table.item(selected_row, 1).text()
        
        if user_id == 1:
            QMessageBox.critical(self, self.tr("Action Not Allowed"), self.tr("The main admin account cannot be deleted."))
            return
        
        reply = QMessageBox.question(self, self.tr("Confirm Deletion"), f"{self.tr('Are you sure you want to delete user')} <b>{username}</b>?")
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_user(user_id):
                QMessageBox.information(self, self.tr("Success"), self.tr("User deleted successfully."))
                self.load_users_data()

    def tr(self, text):
        return QCoreApplication.translate("UsersWidget", text)