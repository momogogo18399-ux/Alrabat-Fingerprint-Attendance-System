import os
import io
import base64
import tempfile
from PIL import Image
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QInputDialog, QLabel, QLineEdit, QComboBox,
    QGroupBox, QFormLayout, QCheckBox, QSpinBox, QDateEdit, QTextEdit,
    QSplitter, QFrame, QProgressBar, QDialog, QDialogButtonBox, QAbstractItemView,
    QFileDialog, QApplication
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QDate, QCoreApplication
from PyQt6.QtGui import QFont, QColor, QPalette
import pandas as pd

from app.database.simple_hybrid_manager import SimpleHybridManager
from app.fingerprint.zk_manager import ZKManager
from app.core.config_manager import get_config
from app.gui.employee_dialog import EmployeeDialog
from app.gui.history_dialog import HistoryDialog

# --- Worker Thread لتسجيل البصمة في الخلفية ---
class EnrollWorker(QThread):
    success = pyqtSignal(bytes)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, zk_manager, user_id):
        super().__init__()
        self.zk_manager = zk_manager
        self.user_id = user_id
        self._is_running = True

    def run(self):
        try:
            uid = str(self.user_id)
            # enroll_user هي دالة generator في مكتبة pyzk
            for step in self.zk_manager.zk.enroll_user(uid=uid):
                if not self._is_running:
                    self.failure.emit("Enrollment canceled by user.")
                    return

                if step == 1:
                    self.step_update.emit("Enrollment started. Please place a finger on the scanner.")
                elif step == 2:
                    self.step_update.emit("Fingerprint captured. Please place the same finger again.")
                elif step == 3:
                    self.step_update.emit("Fingerprint captured again. Please place the same finger a third time.")
                elif isinstance(step, tuple) and len(step) > 1:
                    fingerprint_template = step[1]
                    self.step_update.emit("Enrollment successful!")
                    self.success.emit(fingerprint_template)
                    return # إنهاء العملية بنجاح
            
            # إذا انتهت الحلقة بدون نجاح
            if self._is_running:
                self.failure.emit("Enrollment failed or timed out. Please try again.")

        except Exception as e:
            self.failure.emit(f"An error occurred during enrollment: {e}")
    
    def stop(self):
        self._is_running = False

# --- الواجهة الرئيسية لإدارة الموظفين ---
class EmployeesWidget(QWidget):
    def __init__(self, user_role, db_manager=None):
        super().__init__()
        self.user_role = user_role
        self.db_manager = db_manager or SimpleHybridManager()
        self.zk_manager = self.initialize_zk_manager()
        self.enroll_worker = None
        self.enroll_msg_box = None
        self.all_employees = []  # تخزين جميع الموظفين للبحث
        
        self.setup_ui()
        self.connect_signals()
        self.load_employees_data()

    def initialize_zk_manager(self):
        try:
            config = get_config()
            ip = config.get('Device', 'ip')
            port = int(config.get('Device', 'port', fallback='4370'))
            password = int(config.get('Device', 'password', fallback='0'))
            return ZKManager(ip, port=port, password=password)
        except Exception as e:
            print(f"Failed to initialize ZKManager: {e}")
            return None

    def setup_ui(self):
        layout = QVBoxLayout(self)
        button_layout = QHBoxLayout()
        self.add_button = QPushButton(f"➕ {self.tr('Add Employee')}")
        self.add_button.setToolTip(self.tr("Create a new employee record"))
        self.import_button = QPushButton(f"📥 {self.tr('Import from Excel')}")
        self.import_button.setToolTip(self.tr("Bulk import employees from an Excel file"))
        self.export_template_button = QPushButton(f"📄 {self.tr('Export Template')}")
        self.export_template_button.setToolTip(self.tr("Export an Excel template for import"))
        self.export_data_button = QPushButton(f"📤 {self.tr('Export All Data')}")
        self.export_data_button.setToolTip(self.tr("Export all employees to Excel"))
        self.export_qr_button = QPushButton(f"📱 {self.tr('Export with QR Codes')}")
        self.export_qr_button.setToolTip(self.tr("Export employees data with QR codes to Excel"))
        self.export_qr_images_button = QPushButton(f"🖼️ {self.tr('Export QR Images')}")
        self.export_qr_images_button.setToolTip(self.tr("Export QR code images as separate files"))
        self.register_fp_button = QPushButton(f"👆 {self.tr('Register Fingerprint')}")
        self.register_fp_button.setToolTip(self.tr("Register fingerprint on a connected ZK device"))
        self.edit_button = QPushButton(f"✏️ {self.tr('Edit Selected')}")
        self.edit_button.setToolTip(self.tr("Edit the selected employee record"))
        self.delete_button = QPushButton(f"🗑️ {self.tr('Delete Selected')}")
        self.delete_button.setToolTip(self.tr("Delete the selected employee record"))
        self.history_button = QPushButton(f"📜 {self.tr('View History')}")
        self.history_button.setToolTip(self.tr("View attendance history of the selected employee"))
        self.qr_button = QPushButton(f"📱 {self.tr('QR Code')}")
        self.qr_button.setToolTip(self.tr("View QR code for the selected employee"))
        self.refresh_button = QPushButton(f"🔄 {self.tr('Refresh')}")
        self.refresh_button.setToolTip(self.tr("Reload the employee list"))
        
        button_layout.addWidget(self.add_button); button_layout.addSpacing(10)
        button_layout.addWidget(self.import_button); button_layout.addWidget(self.export_template_button); button_layout.addWidget(self.export_data_button); button_layout.addWidget(self.export_qr_button); button_layout.addWidget(self.export_qr_images_button); button_layout.addSpacing(10)
        button_layout.addWidget(self.register_fp_button); button_layout.addSpacing(10)
        button_layout.addWidget(self.edit_button); button_layout.addWidget(self.delete_button); button_layout.addWidget(self.history_button); button_layout.addWidget(self.qr_button)
        button_layout.addStretch(); button_layout.addWidget(self.refresh_button)
        layout.addLayout(button_layout)
        
        # إضافة خانة البحث
        search_layout = QHBoxLayout()
        search_label = QLabel(f"🔍 {self.tr('Search Employee:')}")
        search_label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.tr("Search by name, code, department, or phone..."))
        self.search_input.setToolTip(self.tr("Type to search employees quickly"))
        self.search_input.setMinimumWidth(300)
        self.clear_search_button = QPushButton(f"❌ {self.tr('Clear')}")
        self.clear_search_button.setToolTip(self.tr("Clear search and show all employees"))
        self.clear_search_button.setMaximumWidth(80)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.clear_search_button)
        search_layout.addStretch()
        layout.addLayout(search_layout)
        
        if self.user_role not in ['Admin', 'HR']:
            self.add_button.setEnabled(False); self.import_button.setEnabled(False); self.export_template_button.setEnabled(False); self.export_data_button.setEnabled(False)
            self.export_qr_button.setEnabled(False); self.export_qr_images_button.setEnabled(False); self.register_fp_button.setEnabled(False); self.edit_button.setEnabled(False); self.delete_button.setEnabled(False); self.qr_button.setEnabled(False)
        
        self.table = QTableWidget(); self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", 
            self.tr("Code"), 
            self.tr("Full Name"), 
            self.tr("Job Title"), 
            self.tr("Department"), 
            self.tr("Phone Number"),
            self.tr("Attendance Status"),
            self.tr("Last Attendance")
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

    def connect_signals(self):
        self.add_button.clicked.connect(self.add_employee); self.import_button.clicked.connect(self.import_from_excel)
        self.export_template_button.clicked.connect(self.export_template); self.export_data_button.clicked.connect(self.export_all_employees)
        self.export_qr_button.clicked.connect(self.export_employees_with_qr)
        self.export_qr_images_button.clicked.connect(self.export_qr_images)
        self.register_fp_button.clicked.connect(self.register_fingerprint)
        self.edit_button.clicked.connect(self.edit_employee); self.delete_button.clicked.connect(self.delete_employee)
        self.history_button.clicked.connect(self.view_employee_history); self.qr_button.clicked.connect(self.show_qr_code); self.refresh_button.clicked.connect(self.load_employees_data)
        
        # إشارات البحث
        self.search_input.textChanged.connect(self.filter_employees)
        self.clear_search_button.clicked.connect(self.clear_search)
        
    def load_employees_data(self):
        # استخدام الدالة المحسنة إذا كانت متوفرة
        if hasattr(self.db_manager, 'get_employees_with_attendance'):
            employees = self.db_manager.get_employees_with_attendance() or []
        else:
            employees = self.db_manager.get_all_employees() or []
        
        # تخزين جميع الموظفين للبحث
        self.all_employees = employees
        
        # استخدام دالة populate_table الجديدة
        self.populate_table(employees)

    def register_fingerprint(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select an employee to register their fingerprint.")); return

        if not self.zk_manager:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Fingerprint device manager is not initialized. Check config.")); return

        employee_id = int(self.table.item(selected_row, 0).text())
        employee_code = self.table.item(selected_row, 1).text()
        employee_name = self.table.item(selected_row, 2).text()
        
        msg_box = QMessageBox(self); msg_box.setWindowTitle(self.tr("Device Connection")); msg_box.setText(self.tr("Connecting to fingerprint device..."))
        msg_box.setStandardButtons(QMessageBox.StandardButton.NoButton); msg_box.show(); QCoreApplication.processEvents()
        
        if not self.zk_manager.connect():
            msg_box.close()
            QMessageBox.critical(self, self.tr("Connection Failed"), self.tr("Could not connect to the fingerprint device.")); return
        
        msg_box.close()

        self.enroll_msg_box = QMessageBox(self)
        self.enroll_msg_box.setWindowTitle(self.tr("Enrollment in Progress"))
        self.enroll_msg_box.setText(f"{self.tr('Starting enrollment for')} {employee_name}...")
        self.enroll_msg_box.setStandardButtons(QMessageBox.StandardButton.Cancel)
        self.enroll_msg_box.buttonClicked.connect(self.cancel_enrollment)
        self.enroll_msg_box.show()

        self.enroll_worker = EnrollWorker(self.zk_manager, employee_code)
        self.enroll_worker.success.connect(lambda template: self.on_enroll_success(employee_id, template))
        self.enroll_worker.failure.connect(self.on_enroll_failure)
        self.enroll_worker.step_update.connect(self.update_enroll_message)
        self.enroll_worker.finished.connect(self.zk_manager.disconnect)
        self.enroll_worker.finished.connect(self.enroll_msg_box.close)
        self.enroll_worker.start()

    def update_enroll_message(self, message):
        if self.enroll_msg_box:
            self.enroll_msg_box.setInformativeText(self.tr(message))

    def cancel_enrollment(self):
        if self.enroll_worker and self.enroll_worker.isRunning():
            self.enroll_worker.stop()
            self.enroll_worker.terminate() # For immediate stop
            self.enroll_worker.wait()
            print("Enrollment canceled by user.")

    def on_enroll_success(self, employee_id, template):
        try:
            template_str = base64.b64encode(template).decode('utf-8')
            self.db_manager.update_employee_zk_template(employee_id, template_str)
            QMessageBox.information(self, self.tr("Success"), self.tr("Fingerprint enrolled and saved successfully!"))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Database Error"), f"{self.tr('Failed to save the fingerprint template:')}\n{e}")

    def on_enroll_failure(self, error_message):
        QMessageBox.critical(self, self.tr("Enrollment Failed"), error_message)

    def add_employee(self):
        dialog = EmployeeDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data();
            if data and self.db_manager.add_employee(data):
                # إنشاء رمز QR تلقائياً للموظف الجديد
                try:
                    from app.utils.qr_manager import QRCodeManager
                    qr_manager = QRCodeManager()
                    
                    # الحصول على بيانات الموظف المحدثة (مع ID)
                    employee = self.db_manager.get_employee_by_code(data['employee_code'])
                    if employee:
                        # إنشاء رمز QR
                        qr_code = qr_manager.generate_qr_code(employee)
                        if qr_code:
                            # Save الرمز في قاعدة البيانات
                            self.db_manager.update_employee_qr_code(employee['id'], qr_code)
                            print(f"تم إنشاء رمز QR تلقائياً للموظف: {employee['name']}")
                except Exception as e:
                    print(f"Warning: لم يتم إنشاء رمز QR تلقائياً: {e}")
                
                QMessageBox.information(self, self.tr("Success"), self.tr("Employee added successfully."))
                self.load_employees_data()
            elif data:
                QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to add employee. The code or phone number might already be in use."))
    
    def edit_employee(self):
        selected_row = self.table.currentRow();
        if selected_row < 0: QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select an employee to edit.")); return
        employee_id = int(self.table.item(selected_row, 0).text())
        employee_data = self.db_manager.get_employee_by_id(employee_id)
        dialog = EmployeeDialog(employee_data=employee_data, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            if data and self.db_manager.update_employee(employee_id, data):
                QMessageBox.information(self, self.tr("Success"), self.tr("Employee data updated successfully."))
                self.load_employees_data()
            elif data:
                 QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to update employee data."))

    def delete_employee(self):
        selected_row = self.table.currentRow();
        if selected_row < 0: QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select an employee to delete.")); return
        employee_id = int(self.table.item(selected_row, 0).text()); employee_name = self.table.item(selected_row, 2).text()
        reply = QMessageBox.question(self, self.tr("Confirm Deletion"), f"{self.tr('Are you sure you want to delete the employee:')} <b>{employee_name}</b>?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_employee(employee_id):
                QMessageBox.information(self, self.tr("Success"), self.tr("Employee deleted successfully."))
                self.load_employees_data()
            else:
                QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to delete the employee."))
    
    def view_employee_history(self):
        selected_row = self.table.currentRow();
        if selected_row < 0: QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select an employee to view their history.")); return
        employee_id = int(self.table.item(selected_row, 0).text()); employee_name = self.table.item(selected_row, 2).text()
        history_data = self.db_manager.get_employee_attendance_history(employee_id)
        if not history_data: QMessageBox.information(self, self.tr("No Data"), self.tr("There are no attendance records for this employee.")); return
        dialog = HistoryDialog(employee_name, history_data, self); dialog.exec()
    
    def show_qr_code(self):
        """عرض رمز QR للموظف المحدد"""
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select an employee to view their QR code."))
            return
        
        employee_id = int(self.table.item(selected_row, 0).text())
        employee_data = self.db_manager.get_employee_by_id(employee_id)
        
        if not employee_data:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Employee data not found."))
            return
        
        from app.gui.qr_dialog import QRCodeDialog
        dialog = QRCodeDialog(employee_data, self)
        dialog.exec()
    
    def import_from_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, self.tr("Select Excel File"), "", f"{self.tr('Excel Files (*.xlsx *.xls)')}")
        if not file_path: return
        try:
            df = pd.read_excel(file_path); required_columns = ['employee_code', 'name', 'phone_number']
            if not all(col in df.columns for col in required_columns):
                QMessageBox.critical(self, self.tr("Import Error"), self.tr("The Excel file must contain 'employee_code', 'name', and 'phone_number' columns.")); return
            success_count, fail_count, failed_records = 0, 0, []
            
            # إنشاء مدير QR لإنشاء رموز تلقائياً
            from app.utils.qr_manager import QRCodeManager
            qr_manager = QRCodeManager()
            
            for index, row in df.iterrows():
                try:
                    data = {'employee_code': str(row['employee_code']),'name': row['name'],'phone_number': str(row['phone_number']),'job_title': row.get('job_title', ''),'department': row.get('department', '')}
                    if not all([data['employee_code'], data['name'], data['phone_number']]):
                        fail_count += 1; failed_records.append(f"{row.get('name', 'N/A')} ({self.tr('missing data')})"); continue
                    
                    # Add الموظف
                    if self.db_manager.add_employee(data):
                        # إنشاء رمز QR تلقائياً
                        try:
                            employee = self.db_manager.get_employee_by_code(data['employee_code'])
                            if employee:
                                qr_code = qr_manager.generate_qr_code(employee)
                                if qr_code:
                                    self.db_manager.update_employee_qr_code(employee['id'], qr_code)
                                    print(f"تم إنشاء رمز QR تلقائياً للموظف المستورد: {employee['name']}")
                        except Exception as e:
                            print(f"Warning: لم يتم إنشاء رمز QR للموظف المستورد {data['name']}: {e}")
                        
                        success_count += 1
                    else: 
                        fail_count += 1; failed_records.append(f"{data['name']} ({self.tr('duplicate code or phone')})")
                except Exception as e: fail_count += 1; failed_records.append(f"{row.get('name', 'N/A')} ({str(e)})")
            self.load_employees_data()
            summary_message = f"{self.tr('Import Complete!')}\n\n✅ {self.tr('Successfully added')}: {success_count}\n❌ {self.tr('Failed to add')}: {fail_count}"
            if failed_records: summary_message += f"\n\n{self.tr('Failed records')}:\n- " + "\n- ".join(failed_records)
            QMessageBox.information(self, self.tr("Import Summary"), summary_message)
        except Exception as e: QMessageBox.critical(self, self.tr("File Error"), f"{self.tr('Failed to read the Excel file:')}\n{str(e)}")
    
    def export_template(self):
        file_path, _ = QFileDialog.getSaveFileName(self, self.tr("Save Template File"), "employee_import_template.xlsx", f"{self.tr('Excel Files (*.xlsx)')}")
        if not file_path: return
        try:
            headers = ['employee_code', 'name', 'phone_number', 'job_title', 'department']; df = pd.DataFrame(columns=headers)
            df.to_excel(file_path, index=False, engine='openpyxl')
            QMessageBox.information(self, self.tr("Success"), f"{self.tr('Template file saved successfully at:')}\n{file_path}")
        except Exception as e: QMessageBox.critical(self, self.tr("Error"), f"{self.tr('Failed to save the template file:')}\n{str(e)}")
    
    def export_all_employees(self):
        all_employees = self.db_manager.get_all_employees()
        if not all_employees: QMessageBox.warning(self, self.tr("No Data"), self.tr("There are no employees to export.")); return
        file_path, _ = QFileDialog.getSaveFileName(self, self.tr("Save Employee Data"), f"employees_export_{QDate.currentDate().toString('yyyy-MM-dd')}.xlsx", f"{self.tr('Excel Files (*.xlsx)')}")
        if not file_path: return
        try:
            df = pd.DataFrame(all_employees)
            columns_to_export = ['employee_code', 'name', 'phone_number', 'job_title', 'department', 'status']
            df = df[[col for col in columns_to_export if col in df.columns]]
            df.to_excel(file_path, index=False, engine='openpyxl')
            QMessageBox.information(self, self.tr("Success"), f"{self.tr('Employee data saved successfully at:')}\n{file_path}")
        except Exception as e: QMessageBox.critical(self, self.tr("Error"), f"{self.tr('Failed to export data:')}\n{str(e)}")
    
    def export_employees_with_qr(self):
        """تصدير بيانات الموظفين مع رموز QR إلى ملف Excel"""
        try:
            # الحصول على جميع الموظفين
            all_employees = self.db_manager.get_all_employees()
            if not all_employees:
                QMessageBox.warning(self, self.tr("No Data"), self.tr("There are no employees to export."))
                return
            
            # اختيار مكان حفظ الملف
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                self.tr("Save Employees with QR Codes"), 
                f"employees_with_qr_{QDate.currentDate().toString('yyyy-MM-dd')}.xlsx", 
                f"{self.tr('Excel Files (*.xlsx)')}"
            )
            if not file_path:
                return
            
            # إنشاء مدير QR
            from app.utils.qr_manager import QRCodeManager
            qr_manager = QRCodeManager()
            
            # إعداد شريط التقدم
            progress = QProgressBar()
            progress.setMaximum(len(all_employees))
            progress.setValue(0)
            progress.setVisible(True)
            
            # إنشاء قائمة البيانات للتصدير
            export_data = []
            
            for i, employee in enumerate(all_employees):
                try:
                    # إنشاء رمز QR باستخدام نفس إعدادات QRCodeManager
                    qr_code = qr_manager.generate_qr_code(employee)
                    
                    # إنشاء صورة QR باستخدام نفس الإعدادات
                    qr_pixmap = qr_manager.create_qr_image(qr_code)
                    
                    if qr_pixmap and not qr_pixmap.isNull():
                        # تحويل QPixmap إلى PIL Image مباشرة في الذاكرة
                        # إنشاء BytesIO buffer للصورة
                        qr_buffer = io.BytesIO()
                        qr_pixmap.save(qr_buffer, "PNG")
                        qr_buffer.seek(0)
                        
                        # تحويل إلى base64 للاستخدام لاحقاً
                        qr_base64 = base64.b64encode(qr_buffer.getvalue()).decode()
                        
                        print(f"✅ QR image created successfully for: {employee.get('name', 'Unknown')}")
                    else:
                        print(f"⚠️ Failed to create QR image for: {employee.get('name', 'Unknown')}")
                        qr_base64 = ""
                    
                    # إضافة بيانات الموظف مع رمز QR
                    employee_data = {
                        'ID': employee.get('id', ''),
                        'Employee Code': employee.get('employee_code', ''),
                        'Full Name': employee.get('name', ''),
                        'Job Title': employee.get('job_title', ''),
                        'Department': employee.get('department', ''),
                        'Phone Number': employee.get('phone_number', ''),
                        'Email': employee.get('email', ''),
                        'Status': employee.get('status', 'Active'),
                        'QR Code Data': qr_code if qr_code else 'Error generating QR',
                        'QR Code Image (Base64)': qr_base64,
                        'Created Date': employee.get('created_at', ''),
                        'Last Updated': employee.get('updated_at', '')
                    }
                    
                    export_data.append(employee_data)
                    
                    # تحديث شريط التقدم
                    progress.setValue(i + 1)
                    QApplication.processEvents()  # تحديث الواجهة
                    
                except Exception as e:
                    print(f"❌ General error processing employee {employee.get('name', 'Unknown')}: {e}")
                    # إضافة الموظف بدون رمز QR في حالة الخطأ
                    employee_data = {
                        'ID': employee.get('id', ''),
                        'Employee Code': employee.get('employee_code', ''),
                        'Full Name': employee.get('name', ''),
                        'Job Title': employee.get('job_title', ''),
                        'Department': employee.get('department', ''),
                        'Phone Number': employee.get('phone_number', ''),
                        'Email': employee.get('email', ''),
                        'Status': employee.get('status', 'Active'),
                        'QR Code Data': f'Error: {str(e)[:50]}',
                        'QR Code Image (Base64)': '',
                        'Created Date': employee.get('created_at', ''),
                        'Last Updated': employee.get('updated_at', '')
                    }
                    export_data.append(employee_data)
            
            # إنشاء DataFrame وتصدير إلى Excel
            df = pd.DataFrame(export_data)
            
            # إنشاء ملف Excel مع تنسيق محسن وصور QR
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Employees with QR Codes', index=False)
                
                # الحصول على ورقة العمل
                worksheet = writer.sheets['Employees with QR Codes']
                
                # تنسيق العناوين
                from openpyxl.styles import Font, PatternFill, Alignment
                from openpyxl.drawing.image import Image as OpenpyxlImage
                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                header_alignment = Alignment(horizontal="center", vertical="center")
                
                # تطبيق التنسيق على العناوين
                for cell in worksheet[1]:
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = header_alignment
                
                # إدراج صور QR في العمود الجديد
                qr_image_col = 'J'  # عمود صور QR
                
                # إضافة عنوان عمود صور QR
                worksheet[f'{qr_image_col}1'] = 'QR Code Image'
                worksheet[f'{qr_image_col}1'].font = header_font
                worksheet[f'{qr_image_col}1'].fill = header_fill
                worksheet[f'{qr_image_col}1'].alignment = header_alignment
                
                # إدراج صور QR
                for i, employee in enumerate(export_data):
                    row_num = i + 2  # الصف الأول للعناوين
                    
                    if employee.get('QR Code Image (Base64)'):
                        try:
                            # تحويل base64 إلى صورة مباشرة في الذاكرة
                            qr_base64 = employee['QR Code Image (Base64)']
                            qr_bytes = base64.b64decode(qr_base64)
                            
                            # استخدام BytesIO مباشرة
                            img_stream = io.BytesIO(qr_bytes)
                            img_stream.seek(0)
                            
                            # إدراج الصورة في Excel مباشرة من BytesIO
                            img = OpenpyxlImage(img_stream)
                            img.width = 100
                            img.height = 100
                            
                            # تحديد موقع الصورة مع تحسين الموقع
                            cell_ref = f'{qr_image_col}{row_num}'
                            worksheet.add_image(img, cell_ref)
                            
                            # ضبط ارتفاع الصف لاستيعاب الصورة
                            worksheet.row_dimensions[row_num].height = 75
                            
                            print(f"✅ QR image inserted for: {employee.get('Full Name', 'Unknown')}")
                            
                        except Exception as img_error:
                            print(f"⚠️ Failed to insert QR image for {employee.get('Full Name', 'Unknown')}: {img_error}")
                            worksheet[f'{qr_image_col}{row_num}'] = 'Image Error'
                    else:
                        worksheet[f'{qr_image_col}{row_num}'] = 'No QR Image'
                
                # ضبط عرض الأعمدة
                column_widths = {
                    'A': 10,  # ID
                    'B': 15,  # Employee Code
                    'C': 25,  # Full Name
                    'D': 20,  # Job Title
                    'E': 20,  # Department
                    'F': 15,  # Phone Number
                    'G': 25,  # Email
                    'H': 10,  # Status
                    'I': 50,  # QR Code Data
                    'J': 20,  # QR Code Image - زيادة العرض لاستيعاب الصور بشكل أفضل
                    'K': 15,  # Created Date
                    'L': 15   # Last Updated
                }
                
                for col, width in column_widths.items():
                    worksheet.column_dimensions[col].width = width
            
            # رسالة نجاح
            success_message = f"""✅ {self.tr('Export completed successfully!')}

📊 {self.tr('Exported data:')}
• {self.tr('Total employees')}: {len(export_data)}
• {self.tr('File location')}: {file_path}

📱 {self.tr('QR Codes included:')}
• {self.tr('QR code data')} (text format)
• {self.tr('QR code images')} (base64 format - hidden column)

💡 {self.tr('Tips:')}
• {self.tr('You can scan the QR codes using any QR scanner app')}
• {self.tr('The QR codes contain employee identification data')}
• {self.tr('Use the data for attendance tracking')}"""
            
            QMessageBox.information(self, self.tr("Export Success"), success_message)
            
        except Exception as e:
            error_message = f"""❌ {self.tr('Export failed!')}

🔍 {self.tr('Error details:')}
{str(e)}

💡 {self.tr('Troubleshooting:')}
• {self.tr('Check if you have write permissions to the selected folder')}
• {self.tr('Make sure the file is not open in another application')}
• {self.tr('Try selecting a different folder')}"""
            
            QMessageBox.critical(self, self.tr("Export Error"), error_message)
            print(f"❌ Error in export_employees_with_qr: {e}")
            import traceback
            traceback.print_exc()
    
    def export_qr_images(self):
        """تصدير صور رموز QR كملفات منفصلة"""
        try:
            # الحصول على جميع الموظفين
            all_employees = self.db_manager.get_all_employees()
            if not all_employees:
                QMessageBox.warning(self, self.tr("No Data"), self.tr("There are no employees to export."))
                return
            
            # اختيار مجلد لحفظ الصور
            folder_path = QFileDialog.getExistingDirectory(
                self, 
                self.tr("Select Folder to Save QR Images"),
                ""
            )
            if not folder_path:
                return
            
            # إنشاء مدير QR
            from app.utils.qr_manager import QRCodeManager
            qr_manager = QRCodeManager()
            
            # إعداد شريط التقدم
            progress = QProgressBar()
            progress.setMaximum(len(all_employees))
            progress.setValue(0)
            progress.setVisible(True)
            
            success_count = 0
            failed_count = 0
            failed_employees = []
            
            for i, employee in enumerate(all_employees):
                try:
                    # إنشاء رمز QR للموظف
                    qr_code = qr_manager.generate_qr_code(employee)
                    
                    # إنشاء صورة QR
                    qr_pixmap = qr_manager.create_qr_image(qr_code)
                    
                    if qr_pixmap and not qr_pixmap.isNull():
                        # إنشاء اسم الملف
                        employee_code = employee.get('employee_code', str(employee.get('id', '')))
                        employee_name = employee.get('name', 'Unknown')
                        
                        # تنظيف اسم الملف من الأحرف غير المسموحة
                        safe_name = "".join(c for c in employee_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                        safe_name = safe_name.replace(' ', '_')
                        
                        file_name = f"QR_{employee_code}_{safe_name}.png"
                        file_path = os.path.join(folder_path, file_name)
                        
                        # حفظ الصورة
                        if qr_pixmap.save(file_path, "PNG"):
                            success_count += 1
                            print(f"✅ Saved QR image for: {employee_name}")
                        else:
                            failed_count += 1
                            failed_employees.append(f"{employee_name} (Save failed)")
                    else:
                        failed_count += 1
                        failed_employees.append(f"{employee_name} (QR generation failed)")
                    
                    # تحديث شريط التقدم
                    progress.setValue(i + 1)
                    QApplication.processEvents()
                    
                except Exception as e:
                    failed_count += 1
                    failed_employees.append(f"{employee.get('name', 'Unknown')} ({str(e)})")
                    print(f"❌ Error processing employee {employee.get('name', 'Unknown')}: {e}")
            
            # رسالة نجاح
            success_message = f"""✅ {self.tr('QR Images Export completed!')}

📊 {self.tr('Export Summary:')}
• {self.tr('Total employees')}: {len(all_employees)}
• {self.tr('Successfully exported')}: {success_count}
• {self.tr('Failed to export')}: {failed_count}
• {self.tr('Folder location')}: {folder_path}

📱 {self.tr('QR Image Details:')}
• {self.tr('Format')}: PNG
• {self.tr('Naming')}: QR_[EmployeeCode]_[EmployeeName].png
• {self.tr('Size')}: 300x300 pixels (default)

💡 {self.tr('Usage Tips:')}
• {self.tr('You can print these QR codes')}
• {self.tr('Use them for physical attendance tracking')}
• {self.tr('Scan with any QR scanner app')}"""
            
            if failed_employees:
                success_message += f"\n\n❌ {self.tr('Failed employees:')}\n- " + "\n- ".join(failed_employees)
            
            QMessageBox.information(self, self.tr("QR Images Export Success"), success_message)
            
        except Exception as e:
            error_message = f"""❌ {self.tr('QR Images Export failed!')}

🔍 {self.tr('Error details:')}
{str(e)}

💡 {self.tr('Troubleshooting:')}
• {self.tr('Check if you have write permissions to the selected folder')}
• {self.tr('Make sure the folder is not read-only')}
• {self.tr('Try selecting a different folder')}"""
            
            QMessageBox.critical(self, self.tr("QR Images Export Error"), error_message)
            print(f"❌ Error in export_qr_images: {e}")
            import traceback
            traceback.print_exc()
    
    def filter_employees(self, search_text):
        """تصفية الموظفين بناءً على نص البحث"""
        try:
            if not search_text.strip():
                # إذا كان البحث فارغاً، اعرض جميع الموظفين
                self.populate_table(self.all_employees)
                return
            
            search_text = search_text.lower().strip()
            filtered_employees = []
            
            for employee in self.all_employees:
                # البحث في الاسم
                name = str(employee.get('name', '')).lower()
                # البحث في الكود
                code = str(employee.get('employee_code', '')).lower()
                # البحث في القسم
                department = str(employee.get('department', '')).lower()
                # البحث في الهاتف
                phone = str(employee.get('phone', '')).lower()
                # البحث في المسمى الوظيفي
                job_title = str(employee.get('job_title', '')).lower()
                
                # التحقق من وجود النص في أي من الحقول
                if (search_text in name or 
                    search_text in code or 
                    search_text in department or 
                    search_text in phone or 
                    search_text in job_title):
                    filtered_employees.append(employee)
            
            # عرض النتائج المفلترة
            self.populate_table(filtered_employees)
            
            # تحديث عدد النتائج في شريط الحالة
            if hasattr(self, 'statusBar') and self.statusBar():
                self.statusBar().showMessage(
                    f"{self.tr('Found')} {len(filtered_employees)} {self.tr('employees matching')} '{search_text}'"
                )
            
        except Exception as e:
            print(f"❌ Error in filter_employees: {e}")
            import traceback
            traceback.print_exc()
    
    def clear_search(self):
        """مسح البحث وعرض جميع الموظفين"""
        try:
            self.search_input.clear()
            self.populate_table(self.all_employees)
            
            if hasattr(self, 'statusBar') and self.statusBar():
                self.statusBar().showMessage(
                    f"{self.tr('Showing all')} {len(self.all_employees)} {self.tr('employees')}"
                )
                
        except Exception as e:
            print(f"❌ Error in clear_search: {e}")
            import traceback
            traceback.print_exc()
    
    def populate_table(self, employees):
        """ملء الجدول بالموظفين المحددين"""
        try:
            self.table.setRowCount(0)
            self.table.setRowCount(len(employees))
            
            for row_idx, employee in enumerate(employees):
                # الأعمدة الأساسية
                self.table.setItem(row_idx, 0, QTableWidgetItem(str(employee['id'])))
                self.table.setItem(row_idx, 1, QTableWidgetItem(str(employee.get('employee_code', ''))))
                self.table.setItem(row_idx, 2, QTableWidgetItem(str(employee.get('name', ''))))
                self.table.setItem(row_idx, 3, QTableWidgetItem(str(employee.get('job_title', ''))))
                self.table.setItem(row_idx, 4, QTableWidgetItem(str(employee.get('department', ''))))
                self.table.setItem(row_idx, 5, QTableWidgetItem(str(employee.get('phone_number', employee.get('phone', '')))))
                
                # أعمدة الحضور الجديدة
                if hasattr(self.db_manager, 'get_employees_with_attendance'):
                    # حالة الحضور
                    attendance_status = employee.get('attendance_status', 'لم يسجل حضور')
                    status_item = QTableWidgetItem(attendance_status)
                    
                    # تلوين الحالة حسب النوع
                    if 'حاضر' in attendance_status:
                        status_item.setBackground(QColor(144, 238, 144))  # أخضر فاتح
                    elif 'انصرف' in attendance_status:
                        status_item.setBackground(QColor(255, 255, 224))  # أصفر فاتح
                    elif 'لم يسجل' in attendance_status:
                        status_item.setBackground(QColor(255, 182, 193))  # أحمر فاتح
                    
                    self.table.setItem(row_idx, 6, status_item)
                    
                    # آخر حضور
                    last_attendance = ''
                    if employee.get('last_attendance_date') and employee.get('last_attendance_time'):
                        last_attendance = f"{employee['last_attendance_date']} {employee['last_attendance_time']}"
                    elif employee.get('last_attendance_date'):
                        last_attendance = employee['last_attendance_date']
                    
                    self.table.setItem(row_idx, 7, QTableWidgetItem(last_attendance))
                else:
                    # إذا لم تكن الدالة متوفرة، أعمدة فارغة
                    self.table.setItem(row_idx, 6, QTableWidgetItem('غير متوفر'))
                    self.table.setItem(row_idx, 7, QTableWidgetItem('غير متوفر'))
            
            # إعادة ترتيب الأعمدة
            self.table.resizeColumnsToContents()
            
        except Exception as e:
            print(f"❌ Error in populate_table: {e}")
            import traceback
            traceback.print_exc()
    
    def tr(self, text):
        return QCoreApplication.translate("EmployeesWidget", text)