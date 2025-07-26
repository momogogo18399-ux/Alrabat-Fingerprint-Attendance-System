from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QDialogButtonBox, QMessageBox
)
from PyQt6.QtCore import QCoreApplication

class PasswordDialog(QDialog):
    """نافذة حوار لتغيير كلمة مرور المستخدم."""
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"{self.tr('Change Password for')} {username}")

        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        form.addRow(f"{self.tr('New Password')}:", self.new_password_input)
        form.addRow(f"{self.tr('Confirm Password')}:", self.confirm_password_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_password(self):
        """يتحقق من صحة كلمة المرور الجديدة ويعيدها."""
        new_pass = self.new_password_input.text()
        confirm_pass = self.confirm_password_input.text()

        if not new_pass or not confirm_pass:
            QMessageBox.warning(self, self.tr("Error"), self.tr("Password fields cannot be empty."))
            return None
        
        if new_pass != confirm_pass:
            QMessageBox.warning(self, self.tr("Error"), self.tr("Passwords do not match."))
            return None

        return new_pass
    
    def tr(self, text):
        return QCoreApplication.translate("PasswordDialog", text)