from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QDialogButtonBox, QMessageBox, QComboBox
)
from PyQt6.QtCore import QCoreApplication

class UserDialog(QDialog):
    """نافذة حوار لإضافة أو تعديل مستخدم."""
    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)
        self.is_edit_mode = user_data is not None
        self.user_data = user_data or {}

        title = self.tr("Edit User") if self.is_edit_mode else self.tr("Add New User")
        self.setWindowTitle(title)
        
        # إنشاء الحقول
        self.username_input = QLineEdit(self.user_data.get('username', ''))
        if self.is_edit_mode:
            self.username_input.setReadOnly(True) # لا يمكن تغيير اسم المستخدم

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        if self.is_edit_mode:
            self.password_input.setPlaceholderText(self.tr("Leave empty to keep current password"))
            self.password_input.setDisabled(True) # تعطيل حقل كلمة المرور في وضع التعديل

        self.role_combo = QComboBox()
        self.role_combo.addItems(['Viewer', 'Manager', 'HR', 'Admin'])
        if self.is_edit_mode:
            self.role_combo.setCurrentText(self.user_data.get('role', 'Viewer'))

        # التصميم
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow(f"{self.tr('Username')} (*):", self.username_input)
        if not self.is_edit_mode:
             form.addRow(f"{self.tr('Password')} (*):", self.password_input)
        form.addRow(f"{self.tr('Role')}:", self.role_combo)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        """يتحقق من البيانات ويعيدها."""
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, self.tr("Missing Information"), self.tr("Username cannot be empty."))
            return None

        data = {'username': username, 'role': self.role_combo.currentText()}
        
        if self.is_edit_mode:
            data['id'] = self.user_data['id']
        else: # وضع الإضافة
            password = self.password_input.text()
            if not password:
                QMessageBox.warning(self, self.tr("Missing Information"), self.tr("Password cannot be empty in add mode."))
                return None
            data['password'] = password
        
        return data
    
    def tr(self, text):
        return QCoreApplication.translate("UserDialog", text)