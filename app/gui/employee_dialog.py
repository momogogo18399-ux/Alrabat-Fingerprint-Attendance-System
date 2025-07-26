from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, 
    QDialogButtonBox, QMessageBox, QTextEdit, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import QCoreApplication
from app.database.database_manager import DatabaseManager # <-- استيراد جديد

class EmployeeDialog(QDialog):
    """
    نافذة حوار لإضافة موظف جديد أو تعديل بياناته، مع إمكانية إعادة تعيين الجهاز.
    """
    def __init__(self, employee_data=None, parent=None):
        super().__init__(parent)
        
        self.db_manager = DatabaseManager() # <-- إضافة نسخة من مدير قاعدة البيانات
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
        
        # عرض بصمة الويب والتوكن (للقراءة فقط)
        web_fingerprint_info = self.employee_data.get('web_fingerprint', '')
        device_token_info = self.employee_data.get('device_token', '')
        
        self.device_info_display = QTextEdit()
        if web_fingerprint_info or device_token_info:
            display_text = (
                f"Web Fingerprint: {web_fingerprint_info[:30]}...\n\n"
                f"Device Token: {device_token_info}"
            )
            self.device_info_display.setText(display_text)
        else:
            self.device_info_display.setPlaceholderText(
                self.tr("Leave this field empty. It will be auto-filled on the employee's first successful web check-in.")
            )
        
        self.device_info_display.setReadOnly(True)
        self.device_info_display.setFixedHeight(100)

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

        # --- بداية التعديل: إضافة زر إعادة التعيين ---
        # إنشاء حاوية أفقية للأزرار
        action_buttons_layout = QHBoxLayout()
        
        self.reset_device_button = QPushButton(f"🔄 {self.tr('Reset Web Device')}")
        self.reset_device_button.setToolTip(self.tr("Clears the registered web device, allowing the employee to check in from a new device/browser."))
        self.reset_device_button.clicked.connect(self.reset_device)
        
        # إظهار الزر فقط في وضع التعديل وإذا كان هناك جهاز مسجل
        if not self.is_edit_mode or not device_token_info:
            self.reset_device_button.hide()

        action_buttons_layout.addWidget(self.reset_device_button)
        action_buttons_layout.addStretch()
        layout.addLayout(action_buttons_layout)
        # --- نهاية التعديل ---

        # أزرار OK و Cancel القياسية
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def reset_device(self):
        """
        يسأل للتأكيد ثم يقوم بمسح معلومات جهاز الموظف.
        """
        reply = QMessageBox.question(
            self,
            self.tr("Confirm Device Reset"),
            self.tr("Are you sure you want to allow this employee to register a new device/browser?\n\nThis will delete their current web device registration."),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            employee_id = self.employee_data.get('id')
            if employee_id:
                if self.db_manager.reset_employee_device_info(employee_id):
                    QMessageBox.information(self, self.tr("Success"), self.tr("Device has been reset. The employee can now register a new device on their next web check-in."))
                    # تحديث الواجهة لتعكس التغيير
                    self.device_info_display.clear()
                    self.reset_device_button.hide()
                else:
                    QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to reset the device in the database."))
    
    def get_data(self):
        # ... (نفس كود هذه الدالة بدون تغيير) ...
        code = self.code_input.text().strip()
        name = self.name_input.text().strip()
        phone = self.phone_number_input.text().strip()

        if not code or not name or not phone:
            QMessageBox.warning(self, self.tr("Missing Information"), self.tr("The 'Employee Code', 'Full Name', and 'Phone Number' fields cannot be empty."))
            return None
            
        data = {
            'employee_code': code,
            'name': name,
            'job_title': self.job_title_input.text().strip(),
            'department': self.department_input.text().strip(),
            'phone_number': phone,
        }
        
        if self.is_edit_mode:
            data['id'] = self.employee_data['id']
            # نحافظ على البيانات القديمة إذا كانت موجودة
            data['web_fingerprint'] = self.employee_data.get('web_fingerprint')
            data['device_token'] = self.employee_data.get('device_token')
            
        return data

    def tr(self, text):
        return QCoreApplication.translate("EmployeeDialog", text)