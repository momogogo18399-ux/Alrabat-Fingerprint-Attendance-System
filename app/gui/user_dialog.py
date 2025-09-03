from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QDialogButtonBox, QMessageBox, QComboBox
)
from PyQt6.QtCore import QCoreApplication

class UserDialog(QDialog):
    """
    نافذة حوار لAdd مستخدم برنامج جديد أو Edit دوره.
    """
    def __init__(self, user_data=None, parent=None):
        super().__init__(parent)
        self.is_edit_mode = user_data is not None
        self.user_data = user_data or {}

        title = self.tr("Edit User Role") if self.is_edit_mode else self.tr("Add New User")
        self.setWindowTitle(title)
        self.setMinimumWidth(350)
        
        # إنشاء الحقول
        self.username_input = QLineEdit(self.user_data.get('username', ''))
        if self.is_edit_mode:
            self.username_input.setReadOnly(True) # لا يمكن تغيير اسم المستخدم بعد إنشائه

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText(self.tr("Enter a strong password"))
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)

        self.role_combo = QComboBox()
        self.role_combo.addItems(['Viewer', 'Manager', 'HR', 'Admin', 'Scanner'])
        if self.is_edit_mode:
            self.role_combo.setCurrentText(self.user_data.get('role', 'Viewer'))

        # التصميم
        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow(f"{self.tr('Username')} (*):", self.username_input)
        
        # عرض حقل كلمة المرور فقط في وضع الAdd
        if not self.is_edit_mode:
             form.addRow(f"{self.tr('Password')} (*):", self.password_input)
             
        form.addRow(f"{self.tr('Role')}:", self.role_combo)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self):
        """يتحقق من صحة البيانات المدخلة ويعيدها."""
        username = self.username_input.text().strip()
        if not username:
            QMessageBox.warning(self, self.tr("Missing Information"), self.tr("Username cannot be empty."))
            return None

        data = {'username': username, 'role': self.role_combo.currentText()}
        
        if self.is_edit_mode:
            data['id'] = self.user_data['id']
        else: # وضع الAdd يتطلب كلمة مرور
            password = self.password_input.text()
            if not password:
                QMessageBox.warning(self, self.tr("Missing Information"), self.tr("Password is required when adding a new user."))
                return None
            data['password'] = password
        
        return data
    
    def tr(self, text):
        return QCoreApplication.translate("UserDialog", text)