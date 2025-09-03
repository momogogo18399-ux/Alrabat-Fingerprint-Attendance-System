from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QDateEdit, 
    QLabel, QFileDialog, QMessageBox, QComboBox, QGroupBox, QCheckBox, QFrame, QFormLayout, QSpinBox
)
from PyQt6.QtCore import QDate, QCoreApplication, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
import pandas as pd
from app.database.simple_hybrid_manager import SimpleHybridManager

class ReportsWidget(QWidget):
    """
    Professional reporting center مع واجهة ديناميكية وأدوات تحكم متقدمة.
    """
    def __init__(self, db_manager=None):
        super().__init__()
        self.db_manager = db_manager or SimpleHybridManager()
        self.app_settings = self.db_manager.get_all_settings()
        self.setup_ui()
        self.load_employees()

    def setup_ui(self):
        main_layout = QHBoxLayout(self)

        # --- الجزء الأيسر: إعدادات التحكم ---
        controls_layout = QVBoxLayout()
        controls_group = QGroupBox(self.tr("Report Configuration"))
        controls_group.setFixedWidth(380)
        
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapAllRows)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        
        self.report_type_combo = QComboBox()
        self.report_type_combo.addItems([
            self.tr("Comprehensive Attendance Summary"),
            self.tr("Detailed Employee Log"),
            self.tr("Punctuality (Lateness) Report"),
            self.tr("Absence Report"),
            self.tr("Overtime Report"),
            self.tr("Department Summary"),
            self.tr("Top Late Employees"),
            self.tr("Arrival Time Heatmap"),
            self.tr("Employee KPI Dashboard"),
            self.tr("Department Leaderboard")
        ])
        form_layout.addRow(f"<b>{self.tr('Report Type')}:</b>", self.report_type_combo)

        self.employee_combo = QComboBox()
        self.employee_label = QLabel(f"<b>{self.tr('Select Employee')}:</b>")
        form_layout.addRow(self.employee_label, self.employee_combo)
        
        self.start_date_edit = QDateEdit(calendarPopup=True, date=QDate.currentDate().addMonths(-1))
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow(f"{self.tr('From Date')}:", self.start_date_edit)
        self.end_date_edit = QDateEdit(calendarPopup=True, date=QDate.currentDate())
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow(f"{self.tr('To Date')}:", self.end_date_edit)

        self.work_days_group = QGroupBox(self.tr("Work Days (for Absence Report)"))
        work_days_layout = QHBoxLayout()
        days = [self.tr('Mon'), self.tr('Tue'), self.tr('Wed'), self.tr('Thu'), self.tr('Fri'), self.tr('Sat'), self.tr('Sun')]
        self.work_day_checkboxes = [QCheckBox(day) for day in days]
        for i in range(5): self.work_day_checkboxes[i].setChecked(True)
        for cb in self.work_day_checkboxes: work_days_layout.addWidget(cb)
        self.work_days_group.setLayout(work_days_layout)
        form_layout.addRow(self.work_days_group)

        self.overtime_group = QGroupBox(self.tr("Overtime Settings (for Overtime Report)"))
        overtime_layout = QHBoxLayout()
        overtime_layout.addWidget(QLabel(self.tr("Calculate overtime for hours exceeding:")))
        self.standard_hours_spinbox = QSpinBox()
        self.standard_hours_spinbox.setRange(1, 12)
        self.standard_hours_spinbox.setValue(8)
        self.standard_hours_spinbox.setSuffix(f" {self.tr('hours/day')}")
        overtime_layout.addWidget(self.standard_hours_spinbox)
        self.overtime_group.setLayout(overtime_layout)
        form_layout.addRow(self.overtime_group)
        
        controls_group.setLayout(form_layout)
        controls_layout.addWidget(controls_group)
        controls_layout.addStretch()

        self.export_button = QPushButton(f"🚀 {self.tr('Generate & Export to Excel')}")
        self.export_button.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.export_button.setMinimumHeight(40)
        controls_layout.addWidget(self.export_button)

        main_layout.addLayout(controls_layout)
        
        # --- الجزء الأيمن: وصف التقرير ---
        self.description_label = QLabel(self.tr("Select a report type to see its description."))
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.description_label.setStyleSheet("font-size: 14px; color: #333; background-color: #f0f8ff; border: 1px solid #d1e7fd; border-radius: 8px; padding: 15px;")
        main_layout.addWidget(self.description_label, 1)
        
        # ربط الإشارات
        self.report_type_combo.currentIndexChanged.connect(self.on_report_type_change)
        self.export_button.setToolTip(self.tr("Generate the selected report for the chosen period and export to Excel."))
        self.export_button.clicked.connect(self.generate_report)
        self.on_report_type_change()

    def load_employees(self):
        employees = self.db_manager.get_all_employees() or []
        self.employee_combo.clear()
        for emp in employees:
            self.employee_combo.addItem(f"{emp['name']} ({emp['employee_code']})", emp['id'])

    def on_report_type_change(self):
        report_index = self.report_type_combo.currentIndex()
        is_employee_report = report_index == 1
        is_absence_report = report_index == 3
        is_overtime_report = report_index == 4
        
        self.employee_label.setVisible(is_employee_report)
        self.employee_combo.setVisible(is_employee_report)
        self.work_days_group.setVisible(is_absence_report)
        self.overtime_group.setVisible(is_overtime_report)
        
        descriptions = [
            self.tr("Generates a summary of total work hours and attendance days for all employees."),
            self.tr("Generates a detailed, day-by-day log for a single selected employee."),
            self.tr("Analyzes check-in times to identify employees who were late, showing count and total minutes."),
            self.tr("Identifies employees who were absent on the selected official work days."),
            self.tr("Identifies employees who worked more than the standard daily hours and calculates their overtime."),
            self.tr("Aggregated attendance metrics grouped by department."),
            self.tr("Ranks employees with the highest total lateness in minutes."),
            self.tr("Heatmap of first check-in time distribution across days and hours."),
            self.tr("Key KPIs by employee: attendance days, total hours, avg hours, lateness count."),
            self.tr("Ranking of departments by total hours, avg hours, and days with presence.")
        ]
        self.description_label.setText(f"<h3>{self.report_type_combo.currentText()}</h3><p>{descriptions[report_index]}</p>")
    
    def generate_report(self):
        # مؤشر انشغال وتعطيل زر التصدير أثناء العمل
        self.export_button.setEnabled(False)
        self.export_button.setText(self.tr("Generating...") + " ⏳")
        QApplication.processEvents()
        report_index = self.report_type_combo.currentIndex()
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

        try:
            if report_index == 0: self.generate_comprehensive_report(start_date, end_date)
            elif report_index == 1:
                employee_id = self.employee_combo.currentData()
                if not employee_id: QMessageBox.warning(self, self.tr("Selection Missing"), self.tr("Please select an employee.")); return
                self.generate_employee_log_report(employee_id, start_date, end_date)
            elif report_index == 2: self.generate_lateness_report(start_date, end_date)
            elif report_index == 3: self.generate_absence_report(start_date, end_date)
            elif report_index == 4: self.generate_overtime_report(start_date, end_date)
            elif report_index == 5: self.generate_department_summary(start_date, end_date)
            elif report_index == 6: self.generate_top_late_employees(start_date, end_date)
            elif report_index == 7: self.generate_heatmap_report(start_date, end_date)
            elif report_index == 8: self.generate_employee_kpi(start_date, end_date)
            elif report_index == 9: self.generate_department_leaderboard(start_date, end_date)
        finally:
            self.export_button.setEnabled(True)
            self.export_button.setText(f"🚀 {self.tr('Generate & Export to Excel')}")
            QApplication.processEvents()

    def generate_comprehensive_report(self, start_date, end_date):
        data = self.db_manager.get_comprehensive_attendance_report(start_date, end_date)
        if not data: QMessageBox.information(self, self.tr("No Data"), self.tr("No attendance data found for this period.")); return
        self.save_dataframe_to_excel(pd.DataFrame(data), "Comprehensive_Attendance_Summary")

    def generate_employee_log_report(self, employee_id, start_date, end_date):
        data = self.db_manager.get_employee_detailed_log(employee_id, start_date, end_date)
        if not data: QMessageBox.information(self, self.tr("No Data"), self.tr("No attendance log found for this employee in this period.")); return
        df = pd.DataFrame(data)
        total_hours = df['work_duration_hours'].sum(); attendance_days = df['date'].nunique()
        summary_df = pd.DataFrame([{'date': '---'}, {'date': self.tr("Total Attendance Days"), 'check_time': attendance_days}, {'date': self.tr("Total Work Hours"), 'check_time': round(total_hours, 2)}])
        df_final = pd.concat([df, summary_df], ignore_index=True)
        employee_name = self.employee_combo.currentText().split(' (')[0].replace(" ", "_")
        self.save_dataframe_to_excel(df_final, f"Detailed_Log_{employee_name}")
    
    def generate_lateness_report(self, start_date, end_date):
        work_start_time = self.app_settings.get('work_start_time', '08:30:00')
        allowance = int(self.app_settings.get('late_allowance_minutes', 15))
        data = self.db_manager.get_lateness_report(start_date, end_date, work_start_time, allowance)
        if not data: QMessageBox.information(self, self.tr("No Data"), self.tr("No late records found for this period.")); return
        for record in data: record['lateness_entries'] = ", ".join(record['lateness_entries'])
        self.save_dataframe_to_excel(pd.DataFrame(data), "Punctuality_Lateness_Report")

    def generate_absence_report(self, start_date, end_date):
        selected_work_days = [i for i, cb in enumerate(self.work_day_checkboxes) if cb.isChecked()]
        if not selected_work_days: QMessageBox.warning(self, self.tr("Input Missing"), self.tr("Please select at least one work day.")); return
        data = self.db_manager.get_absence_report(start_date, end_date, selected_work_days)
        if not data: QMessageBox.information(self, self.tr("No Data"), self.tr("No absence records found for this period.")); return
        self.save_dataframe_to_excel(pd.DataFrame(data), "Absence_Report")
        
    def generate_overtime_report(self, start_date, end_date):
        standard_hours = self.standard_hours_spinbox.value()
        data = self.db_manager.get_overtime_report(start_date, end_date, standard_hours)
        if not data: QMessageBox.information(self, self.tr("No Data"), self.tr("No overtime records found for this period.")); return
        df = pd.DataFrame(data)
        df['overtime_hours'] = df['overtime_hours'].round(2)
        self.save_dataframe_to_excel(df, "Overtime_Report")

    def save_dataframe_to_excel(self, df: pd.DataFrame, report_name: str):
        start_date = self.start_date_edit.date().toString("yyyyMMdd"); end_date = self.end_date_edit.date().toString("yyyyMMdd")
        default_filename = f"{report_name}_{start_date}_to_{end_date}.xlsx"
        file_path, _ = QFileDialog.getSaveFileName(self, self.tr("Save Report"), default_filename, f"{self.tr('Excel Files (*.xlsx)')}")
        if not file_path: return

        try:
            df.rename(columns={
                'employee_code': self.tr('Employee Code'), 'name': self.tr('Name'), 'attendance_days': self.tr('Attendance Days'),
                'total_work_hours': self.tr('Total Work Hours'), 'avg_daily_hours': self.tr('Avg Daily Hours'),
                'date': self.tr('Date'), 'check_time': self.tr('Time'), 'type': self.tr('Action'),
                'work_duration_hours': self.tr('Work Duration (H)'), 'location_name': self.tr('Location'),
                'notes': self.tr('Notes'), 'late_count': self.tr('Late Count'), 'total_late_minutes': self.tr('Total Late (min)'),
                'lateness_entries': self.tr('Late Entries'), 'absence_count': self.tr('Absence Count'), 'absent_dates': self.tr('Absent Dates'),
                'overtime_hours': self.tr('Overtime (H)')
            }, inplace=True)
            # كتابة مع تحسينات الشكل: تجميد الصف الأول وتوسيع الأعمدة
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Report')
                ws = writer.sheets['Report']
                ws.freeze_panes = ws['A2']
                for column_cells in ws.columns:
                    max_length = 0
                    column_letter = column_cells[0].column_letter
                    for cell in column_cells:
                        try:
                            cell_length = len(str(cell.value)) if cell.value is not None else 0
                            if cell_length > max_length:
                                max_length = cell_length
                        except Exception:
                            pass
                    ws.column_dimensions[column_letter].width = min(max(12, max_length + 2), 50)
            QMessageBox.information(self, self.tr("Success"), f"{self.tr('Report saved successfully!')}\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), f"{self.tr('Failed to save report:')}\n{str(e)}")

    def tr(self, text):
        return QCoreApplication.translate("ReportsWidget", text)

    # --- تقارير جديدة ---
    def generate_department_summary(self, start_date, end_date):
        data = self.db_manager.get_department_summary(start_date, end_date)
        if not data:
            QMessageBox.information(self, self.tr("No Data"), self.tr("No department data found for this period."))
            return
        self.save_dataframe_to_excel(pd.DataFrame(data), "Department_Summary")

    def generate_top_late_employees(self, start_date, end_date):
        work_start_time = self.app_settings.get('work_start_time', '08:30:00')
        allowance = int(self.app_settings.get('late_allowance_minutes', 15))
        data = self.db_manager.get_top_late_employees(start_date, end_date, work_start_time, allowance, top_n=10)
        if not data:
            QMessageBox.information(self, self.tr("No Data"), self.tr("No lateness data found for this period."))
            return
        for record in data:
            record['lateness_entries'] = ", ".join(record['lateness_entries'])
        self.save_dataframe_to_excel(pd.DataFrame(data), "Top_Late_Employees")

    def generate_heatmap_report(self, start_date, end_date):
        # استخراج أول وقت Check-In لكل موظف يوميًا ثم بناء مصفوفة ساعات مقابل أيام
        records = self.db_manager.execute_query(
            """
            SELECT a.date, MIN(a.check_time) AS first_time
            FROM attendance a
            WHERE a.type = 'Check-In' AND a.date BETWEEN ? AND ?
            GROUP BY a.date
            ORDER BY a.date ASC
            """,
            (start_date, end_date), fetchall=True
        ) or []
        if not records:
            QMessageBox.information(self, self.tr("No Data"), self.tr("No attendance data found for this period."))
            return
        # تحويل إلى توزيع ساعات
        from collections import Counter
        hour_counts = Counter()
        for r in records:
            try:
                hour = int(str(r['first_time'])[0:2])
                hour_counts[hour] += 1
            except Exception:
                continue
        df = pd.DataFrame(sorted(hour_counts.items()), columns=['Hour', 'Count'])
        self.save_dataframe_to_excel(df, "Arrival_Time_Heatmap")

    def generate_employee_kpi(self, start_date, end_date):
        # جمع KPIs بالاعتماد على دوال متوفرة
        attendance_summary = self.db_manager.get_comprehensive_attendance_report(start_date, end_date) or []
        work_start_time = self.app_settings.get('work_start_time', '08:30:00')
        allowance = int(self.app_settings.get('late_allowance_minutes', 15))
        lateness = self.db_manager.get_lateness_report(start_date, end_date, work_start_time, allowance) or []

        # خرائط للدمج
        code_to_summary = {r['employee_code']: r for r in attendance_summary}
        code_to_late = {r['employee_code']: r for r in lateness}

        rows = []
        for code, summary in code_to_summary.items():
            row = {
                'employee_code': code,
                'name': summary['name'],
                'attendance_days': summary.get('attendance_days', 0),
                'total_work_hours': summary.get('total_work_hours', 0),
                'avg_daily_hours': summary.get('avg_daily_hours', 0),
                'late_count': 0,
                'total_late_minutes': 0,
            }
            late_info = code_to_late.get(code)
            if late_info:
                row['late_count'] = late_info.get('late_count', 0)
                row['total_late_minutes'] = late_info.get('total_late_minutes', 0)
            rows.append(row)

        if not rows:
            QMessageBox.information(self, self.tr("No Data"), self.tr("No KPI data found for this period."))
            return
        self.save_dataframe_to_excel(pd.DataFrame(rows), "Employee_KPI_Dashboard")

    def generate_department_leaderboard(self, start_date, end_date):
        data = self.db_manager.get_department_summary(start_date, end_date)
        if not data:
            QMessageBox.information(self, self.tr("No Data"), self.tr("No department data found for this period."))
            return
        # ترتيب تنازلي بإجمالي الساعات ثم متوسط الساعات
        df = pd.DataFrame(data).sort_values(by=['total_work_hours', 'avg_daily_hours'], ascending=[False, False])
        self.save_dataframe_to_excel(df, "Department_Leaderboard")