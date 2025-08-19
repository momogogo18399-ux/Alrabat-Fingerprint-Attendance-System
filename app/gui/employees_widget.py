from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QInputDialog, QLabel, QLineEdit, QComboBox,
    QGroupBox, QFormLayout, QCheckBox, QSpinBox, QDateEdit, QTextEdit,
    QSplitter, QFrame, QProgressBar, QDialog, QDialogButtonBox, QAbstractItemView,
    QFileDialog
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QDate, QCoreApplication
from PyQt6.QtGui import QFont, QColor, QPalette
import pandas as pd
import base64

from app.database.database_manager import DatabaseManager
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
    def __init__(self, user_role):
        super().__init__()
        self.user_role = user_role
        self.db_manager = DatabaseManager()
        self.zk_manager = self.initialize_zk_manager()
        self.enroll_worker = None
        self.enroll_msg_box = None
        
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
        button_layout.addWidget(self.import_button); button_layout.addWidget(self.export_template_button); button_layout.addWidget(self.export_data_button); button_layout.addSpacing(10)
        button_layout.addWidget(self.register_fp_button); button_layout.addSpacing(10)
        button_layout.addWidget(self.edit_button); button_layout.addWidget(self.delete_button); button_layout.addWidget(self.history_button); button_layout.addWidget(self.qr_button)
        button_layout.addStretch(); button_layout.addWidget(self.refresh_button)
        layout.addLayout(button_layout)
        
        if self.user_role not in ['Admin', 'HR']:
            self.add_button.setEnabled(False); self.import_button.setEnabled(False); self.export_template_button.setEnabled(False); self.export_data_button.setEnabled(False)
            self.register_fp_button.setEnabled(False); self.edit_button.setEnabled(False); self.delete_button.setEnabled(False); self.qr_button.setEnabled(False)
        
        self.table = QTableWidget(); self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", self.tr("Code"), self.tr("Full Name"), self.tr("Job Title"), self.tr("Department"), self.tr("Phone Number")])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers); self.table.setSortingEnabled(True)
        layout.addWidget(self.table)

    def connect_signals(self):
        self.add_button.clicked.connect(self.add_employee); self.import_button.clicked.connect(self.import_from_excel)
        self.export_template_button.clicked.connect(self.export_template); self.export_data_button.clicked.connect(self.export_all_employees)
        self.register_fp_button.clicked.connect(self.register_fingerprint)
        self.edit_button.clicked.connect(self.edit_employee); self.delete_button.clicked.connect(self.delete_employee)
        self.history_button.clicked.connect(self.view_employee_history); self.qr_button.clicked.connect(self.show_qr_code); self.refresh_button.clicked.connect(self.load_employees_data)
        
    def load_employees_data(self):
        employees = self.db_manager.get_all_employees() or []
        self.table.setRowCount(0); self.table.setRowCount(len(employees))
        for row_idx, employee in enumerate(employees):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(employee['id']))); self.table.setItem(row_idx, 1, QTableWidgetItem(employee.get('employee_code', '')))
            self.table.setItem(row_idx, 2, QTableWidgetItem(employee['name'])); self.table.setItem(row_idx, 3, QTableWidgetItem(employee.get('job_title', '')))
            self.table.setItem(row_idx, 4, QTableWidgetItem(employee.get('department', ''))); self.table.setItem(row_idx, 5, QTableWidgetItem(employee.get('phone_number', '')))

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
                            # حفظ الرمز في قاعدة البيانات
                            self.db_manager.update_employee_qr_code(employee['id'], qr_code)
                            print(f"تم إنشاء رمز QR تلقائياً للموظف: {employee['name']}")
                except Exception as e:
                    print(f"تحذير: لم يتم إنشاء رمز QR تلقائياً: {e}")
                
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
            if data and self.db_manager.update_employee(data):
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
                    
                    # إضافة الموظف
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
                            print(f"تحذير: لم يتم إنشاء رمز QR للموظف المستورد {data['name']}: {e}")
                        
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
    
    def tr(self, text):
        return QCoreApplication.translate("EmployeesWidget", text)