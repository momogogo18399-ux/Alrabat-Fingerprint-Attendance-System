from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QDialogButtonBox, QMessageBox, QTextEdit, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import QCoreApplication
from app.database.database_manager import DatabaseManager

class EmployeeDialog(QDialog):
    """
    Dialog window to add new employee أو Edit بياناته، مع عرض Information الجهاز الصحيحة.
    """
    def __init__(self, employee_data=None, parent=None):
        super().__init__(parent)
        
        # استخدام النظام الهجين إذا كان متاحاً
        try:
            from app.database.simple_hybrid_manager import SimpleHybridManager
            self.db_manager = SimpleHybridManager()
        except ImportError:
            from app.database.database_manager import DatabaseManager
            self.db_manager = DatabaseManager()
        self.is_edit_mode = employee_data is not None
        self.employee_data = employee_data or {}
        
        title = self.tr("Edit Employee") if self.is_edit_mode else self.tr("Add New Employee")
        self.setWindowTitle(title)
        self.setMinimumWidth(450)

        # إنشاء الحقول
        self.code_input = QLineEdit(self.employee_data.get('employee_code', ''))
        self.name_input = QLineEdit(self.employee_data.get('name', ''))
        self.job_title_input = QLineEdit(self.employee_data.get('job_title', ''))
        self.department_input = QLineEdit(self.employee_data.get('department', ''))
        self.phone_number_input = QLineEdit(self.employee_data.get('phone_number', ''))
        
        # --- بداية الEdit: عرض بصمة Canvas والتوكن معًا ---
        canvas_fingerprint = self.employee_data.get('web_fingerprint', '')
        device_token = self.employee_data.get('device_token', '')
        

        
        self.device_info_display = QTextEdit()
        if canvas_fingerprint or device_token:
            # بناء النص لعرض كلا المعرفين إذا كانا موجودين
            display_text = ""
            if canvas_fingerprint:
                display_text += f"Canvas Fingerprint: {canvas_fingerprint}\n\n"
            if device_token:
                display_text += f"Device Token: {device_token}"
            
            self.device_info_display.setText(display_text.strip())
        else:
            self.device_info_display.setPlaceholderText(
                self.tr("This field will be auto-filled on the employee's first successful web check-in.")
            )
        
        self.device_info_display.setReadOnly(True)
        self.device_info_display.setFixedHeight(100)
        # --- نهاية الEdit ---

        # التصميم
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        form_layout.addRow(f"{self.tr('Employee Code')} (*):", self.code_input)
        form_layout.addRow(f"{self.tr('Full Name')} (*):", self.name_input)
        form_layout.addRow(f"{self.tr('Phone Number')} (*):", self.phone_number_input)
        form_layout.addRow(f"{self.tr('Job Title')}:", self.job_title_input)
        form_layout.addRow(f"{self.tr('Department')}:", self.department_input)
        form_layout.addRow(f"{self.tr('Registered Web Device Info')}:", self.device_info_display)
        
        layout.addLayout(form_layout)

        action_buttons_layout = QHBoxLayout()
        self.reset_device_button = QPushButton(f"🔄 {self.tr('Reset Web Device')}")
        self.reset_device_button.setToolTip(self.tr("Clears the registered web device, allowing the employee to check in from a new device/browser."))
        self.reset_device_button.clicked.connect(self.reset_device)
        
        # إظهار الزر إذا كان في وضع التحرير وأي من المعرفين موجودًا
        if not self.is_edit_mode or not (canvas_fingerprint or device_token):
            self.reset_device_button.hide()
        else:
            self.reset_device_button.show()

        action_buttons_layout.addWidget(self.reset_device_button)
        action_buttons_layout.addStretch()
        layout.addLayout(action_buttons_layout)
        

        
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def reset_device(self):
        # ... (نفس كود هذه الدالة بدون تغيير) ...
        reply = QMessageBox.question(self, self.tr("Confirm Device Reset"), self.tr("Are you sure you want to allow this employee to register a new web device?"), QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            employee_id = self.employee_data.get('id')
            if employee_id and self.db_manager.reset_employee_device_info(employee_id):
                QMessageBox.information(self, self.tr("Success"), self.tr("Device has been reset."))
                self.device_info_display.clear()
                self.device_info_display.setPlaceholderText(self.tr("This field will be auto-filled..."))
                self.reset_device_button.hide()
            else:
                QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to reset the device."))
    
    def get_data(self):
        # ... (نفس كود هذه الدالة بدون تغيير) ...
        code = self.code_input.text().strip(); name = self.name_input.text().strip(); phone = self.phone_number_input.text().strip()
        if not code or not name or not phone:
            QMessageBox.warning(self, self.tr("Missing Information"), self.tr("The 'Employee Code', 'Full Name', and 'Phone Number' are required."))
            return None
        data = {'employee_code': code, 'name': name, 'job_title': self.job_title_input.text().strip(), 'department': self.department_input.text().strip(), 'phone_number': phone}
        if self.is_edit_mode: data['id'] = self.employee_data['id']
        return data

    def tr(self, text):
        return QCoreApplication.translate("EmployeeDialog", text)