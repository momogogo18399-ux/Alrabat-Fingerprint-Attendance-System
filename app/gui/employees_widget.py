from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, 
    QTableWidgetItem, QHeaderView, QMessageBox, QAbstractItemView, QFileDialog
)
from PyQt6.QtCore import QCoreApplication, QDate, QThread, pyqtSignal
import pandas as pd
import base64 # لاستيراد base64

from app.database.database_manager import DatabaseManager
from app.fingerprint.zk_manager import ZKManager # استيراد مدير ZK
from app.core.config_manager import get_config # استيراد الإعدادات
from app.gui.employee_dialog import EmployeeDialog
from app.gui.history_dialog import HistoryDialog

# --- بداية إضافة كلاس العامل (Worker Thread) ---
class EnrollWorker(QThread):
    """
    عامل في خيط منفصل لتشغيل عملية تسجيل البصمة دون تجميد الواجهة.
    """
    success = pyqtSignal(bytes) # إشارة النجاح مع قالب البصمة
    failure = pyqtSignal(str)   # إشارة الفشل مع رسالة الخطأ
    step_update = pyqtSignal(str) # إشارة لتحديث الواجهة برسائل إرشادية

    def __init__(self, zk_manager, user_id):
        super().__init__()
        self.zk_manager = zk_manager
        self.user_id = user_id

    def run(self):
        """
        يبدأ عملية تسجيل بصمة جديدة لمستخدم على الجهاز.
        هذه الدالة تفاعلية وتنتظر وضع الإصبع.
        """
        try:
            uid = str(self.user_id)
            enrollment_generator = self.zk_manager.zk.enroll_user(uid=uid)
            
            fingerprint_template = None
            for step in enrollment_generator:
                if step == 1:
                    self.step_update.emit("Enrollment started. Please place a finger on the scanner.")
                elif step == 2:
                    self.step_update.emit("Fingerprint captured. Please place the same finger again.")
                elif step == 3:
                    self.step_update.emit("Fingerprint captured again. Please place the same finger a third time.")
                elif isinstance(step, tuple) and len(step) > 1:
                    fingerprint_template = step[1]
                    self.step_update.emit("Enrollment successful!")
                    break
            
            if fingerprint_template:
                self.success.emit(fingerprint_template)
            else:
                self.failure.emit("Enrollment failed or was canceled. Please try again.")
        except Exception as e:
            self.failure.emit(f"An error occurred during enrollment: {e}")

# --- نهاية إضافة كلاس العامل ---


class EmployeesWidget(QWidget):
    """
    A comprehensive widget for managing employees.
    """
    def __init__(self, user_role):
        super().__init__()
        self.user_role = user_role
        self.db_manager = DatabaseManager()
        self.zk_manager = self.initialize_zk_manager()
        self.enroll_worker = None # للاحتفاظ بمرجع للعامل
        
        self.setup_ui()
        self.connect_signals()
        self.load_employees_data()

    def initialize_zk_manager(self):
        try:
            config = get_config()
            ip = config.get('Device', 'ip', fallback='')
            port_str = config.get('Device', 'port', fallback='4370')
            password_str = config.get('Device', 'password', fallback='0')
            port = int(port_str)
            password = int(password_str)
            return ZKManager(ip, port=port, password=password)
        except Exception as e:
            print(f"Failed to initialize ZKManager: {e}")
            return None

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        button_layout = QHBoxLayout()
        self.add_button = QPushButton(f"➕ {self.tr('Add Employee')}")
        self.import_button = QPushButton(f"📥 {self.tr('Import from Excel')}")
        self.export_template_button = QPushButton(f"📄 {self.tr('Export Template')}")
        self.export_data_button = QPushButton(f"📤 {self.tr('Export All Data')}")
        self.register_fp_button = QPushButton(f"👆 {self.tr('Register Fingerprint')}")
        self.edit_button = QPushButton(f"✏️ {self.tr('Edit Selected')}")
        self.delete_button = QPushButton(f"🗑️ {self.tr('Delete Selected')}")
        self.history_button = QPushButton(f"📜 {self.tr('View History')}")
        self.refresh_button = QPushButton(f"🔄 {self.tr('Refresh')}")

        button_layout.addWidget(self.add_button); button_layout.addSpacing(20)
        button_layout.addWidget(self.import_button); button_layout.addWidget(self.export_template_button); button_layout.addWidget(self.export_data_button); button_layout.addSpacing(20)
        button_layout.addWidget(self.register_fp_button); button_layout.addSpacing(20)
        button_layout.addWidget(self.edit_button); button_layout.addWidget(self.delete_button); button_layout.addWidget(self.history_button)
        button_layout.addStretch(); button_layout.addWidget(self.refresh_button)
        layout.addLayout(button_layout)
        
        if self.user_role not in ['Admin', 'HR']:
            self.add_button.setEnabled(False); self.import_button.setEnabled(False); self.export_template_button.setEnabled(False); self.export_data_button.setEnabled(False)
            self.register_fp_button.setEnabled(False); self.edit_button.setEnabled(False); self.delete_button.setEnabled(False)
        
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
        self.history_button.clicked.connect(self.view_employee_history); self.refresh_button.clicked.connect(self.load_employees_data)
        
    def load_employees_data(self):
        employees = self.db_manager.get_all_employees()
        self.table.setRowCount(0); self.table.setRowCount(len(employees))
        for row_idx, employee in enumerate(employees):
            self.table.setItem(row_idx, 0, QTableWidgetItem(str(employee['id']))); self.table.setItem(row_idx, 1, QTableWidgetItem(employee.get('employee_code', '')))
            self.table.setItem(row_idx, 2, QTableWidgetItem(employee['name'])); self.table.setItem(row_idx, 3, QTableWidgetItem(employee['job_title']))
            self.table.setItem(row_idx, 4, QTableWidgetItem(employee['department'])); self.table.setItem(row_idx, 5, QTableWidgetItem(employee['phone_number']))

    def register_fingerprint(self):
        selected_row = self.table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select an employee to register their fingerprint."))
            return

        if not self.zk_manager:
            QMessageBox.critical(self, self.tr("Error"), self.tr("Fingerprint device manager is not initialized. Check config."))
            return

        employee_id = int(self.table.item(selected_row, 0).text())
        employee_code = self.table.item(selected_row, 1).text()
        employee_name = self.table.item(selected_row, 2).text()
        
        # الاتصال بالجهاز
        msg_box = QMessageBox(self); msg_box.setWindowTitle(self.tr("Device Connection")); msg_box.setText(self.tr("Connecting to fingerprint device..."))
        msg_box.setStandardButtons(QMessageBox.StandardButton.NoButton); msg_box.show(); QCoreApplication.processEvents()
        if not self.zk_manager.connect():
            msg_box.close()
            QMessageBox.critical(self, self.tr("Connection Failed"), self.tr("Could not connect to the fingerprint device."))
            return
        
        # إظهار رسالة إرشادية للمستخدم
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
        self.enroll_msg_box.setInformativeText(self.tr(message))

    def cancel_enrollment(self):
        if self.enroll_worker and self.enroll_worker.isRunning():
            self.enroll_worker.terminate()
            self.enroll_worker.wait()
            self.zk_manager.disconnect()
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

    # --- باقي دوال الكلاس ---
    def add_employee(self):
        dialog = EmployeeDialog(parent=self)
        if dialog.exec():
            data = dialog.get_data();
            if data:
                if self.db_manager.add_employee(data): QMessageBox.information(self, self.tr("Success"), self.tr("Employee added successfully.")); self.load_employees_data()
                else: QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to add employee. The code or phone number might already be in use."))
    def edit_employee(self):
        selected_row = self.table.currentRow();
        if selected_row < 0: QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select an employee to edit.")); return
        employee_id = int(self.table.item(selected_row, 0).text()); employee_data = self.db_manager.get_employee_by_id(employee_id)
        dialog = EmployeeDialog(employee_data=employee_data, parent=self)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                if self.db_manager.update_employee(data): QMessageBox.information(self, self.tr("Success"), self.tr("Employee data updated successfully.")); self.load_employees_data()
                else: QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to update employee data."))
    def delete_employee(self):
        selected_row = self.table.currentRow();
        if selected_row < 0: QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select an employee to delete.")); return
        employee_id = int(self.table.item(selected_row, 0).text()); employee_name = self.table.item(selected_row, 2).text()
        reply = QMessageBox.question(self, self.tr("Confirm Deletion"), self.tr("Are you sure you want to delete the employee: ") + f"<b>{employee_name}</b>?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            if self.db_manager.delete_employee(employee_id): QMessageBox.information(self, self.tr("Success"), self.tr("Employee deleted successfully.")); self.load_employees_data()
            else: QMessageBox.critical(self, self.tr("Error"), self.tr("Failed to delete the employee."))
    def view_employee_history(self):
        selected_row = self.table.currentRow();
        if selected_row < 0: QMessageBox.warning(self, self.tr("No Selection"), self.tr("Please select an employee to view their history.")); return
        employee_id = int(self.table.item(selected_row, 0).text()); employee_name = self.table.item(selected_row, 2).text()
        history_data = self.db_manager.get_employee_attendance_history(employee_id)
        if not history_data: QMessageBox.information(self, self.tr("No Data"), self.tr("There are no attendance records for this employee.")); return
        dialog = HistoryDialog(employee_name, history_data, self); dialog.exec()
    def import_from_excel(self):
        file_path, _ = QFileDialog.getOpenFileName(self, self.tr("Select Excel File"), "", f"{self.tr('Excel Files (*.xlsx *.xls)')}")
        if not file_path: return
        try:
            df = pd.read_excel(file_path); required_columns = ['employee_code', 'name', 'phone_number']
            if not all(col in df.columns for col in required_columns):
                QMessageBox.critical(self, self.tr("Import Error"), self.tr("The Excel file must contain 'employee_code', 'name', and 'phone_number' columns.")); return
            success_count = 0; fail_count = 0; failed_records = []
            for index, row in df.iterrows():
                try:
                    data = {'employee_code': str(row['employee_code']),'name': row['name'],'phone_number': str(row['phone_number']),'job_title': row.get('job_title', ''),'department': row.get('department', ''),'device_fingerprint': None}
                    if not all([data['employee_code'], data['name'], data['phone_number']]): failed_records.append(f"{row.get('name', 'N/A')} ({self.tr('missing data')})"); fail_count += 1; continue
                    if not self.db_manager.add_employee(data): fail_count += 1; failed_records.append(f"{data['name']} ({self.tr('duplicate code or phone')})")
                    else: success_count += 1
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
        try:
            all_employees = self.db_manager.get_all_employees()
            if not all_employees: QMessageBox.warning(self, self.tr("No Data"), self.tr("There are no employees to export.")); return
            file_path, _ = QFileDialog.getSaveFileName(self, self.tr("Save Employee Data"), f"employees_export_{QDate.currentDate().toString('yyyy-MM-dd')}.xlsx", f"{self.tr('Excel Files (*.xlsx)')}")
            if not file_path: return
            df = pd.DataFrame(all_employees)
            columns_to_export = ['employee_code', 'name', 'phone_number', 'job_title', 'department', 'status']; df = df[columns_to_export]
            df.to_excel(file_path, index=False, engine='openpyxl')
            QMessageBox.information(self, self.tr("Success"), f"{self.tr('Employee data saved successfully at:')}\n{file_path}")
        except Exception as e: QMessageBox.critical(self, self.tr("Error"), f"{self.tr('Failed to export data:')}\n{str(e)}")
    def tr(self, text):
        return QCoreApplication.translate("EmployeesWidget", text)