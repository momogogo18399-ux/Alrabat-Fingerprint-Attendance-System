import sys
import webbrowser
import pandas as pd
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QApplication, QDateEdit, QHBoxLayout,
    QMessageBox, QFileDialog
)
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QDate, QTime, QCoreApplication, QTranslator, QLocale
from app.gui.employees_widget import EmployeesWidget
from app.gui.reports_widget import ReportsWidget
from app.gui.search_widget import SearchWidget
from app.gui.settings_widget import SettingsWidget
from app.gui.users_widget import UsersWidget
from app.database.database_manager import DatabaseManager
from app.utils.notifier import NotifierThread

class MainWindow(QMainWindow):
    """
    النافذة الرئيسية للتطبيق، تعمل كلوحة تحكم وحاوية لجميع الواجهات الأخرى.
    """
    def __init__(self, user_data: dict, app_instance):
        super().__init__()
        self.user_data = user_data
        self.db_manager = DatabaseManager()
        self.app = app_instance # الاحتفاظ بنسخة من QApplication للتحكم في التطبيق
        self.translator = QTranslator(self) # إنشاء نسخة من المترجم
        
        self.app_settings = self.db_manager.get_all_settings()
        
        # تحميل اللغة الأولية عند بدء التشغيل
        self.initial_load_language()

        # بناء الواجهة والخدمات
        self.rebuild_ui()
        self.start_notifier_service()

    def tr(self, text):
        """دالة مساعدة للترجمة."""
        return QCoreApplication.translate("MainWindow", text)

    def initial_load_language(self):
        """تحمل اللغة المحفوظة في الإعدادات عند فتح البرنامج لأول مرة."""
        lang_code = self.app_settings.get('language', 'en')
        if self.translator.load(QLocale(lang_code), "", "", "translations"):
            self.app.installTranslator(self.translator)
            if lang_code == 'ar':
                self.app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            else:
                self.app.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
        else:
            print(f"Could not load initial translation for: {lang_code}")

    def rebuild_ui(self):
        """
        تعيد بناء كل الواجهة (التبويبات) لتطبيق التغييرات مثل اللغة.
        """
        window_title = self.tr("Dashboard") + f" - [{self.user_data.get('username')}] - ({self.user_data.get('role')})"
        self.setWindowTitle(window_title)
        self.setGeometry(100, 100, 1280, 720)
        
        self.setup_ui_elements()
        self.connect_signals()
        
        # استدعاء تحديث الداشبورد بعد إعادة البناء
        if hasattr(self, 'date_selector'):
            self.update_dashboard_table()

    def setup_ui_elements(self):
        """
        ينشئ وينظم جميع عناصر واجهة المستخدم والتبويبات.
        """
        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Arial", 11))
        
        # --- تبويب لوحة التحكم (Dashboard) ---
        self.dashboard_tab = QWidget()
        main_layout = QVBoxLayout(self.dashboard_tab)
        top_layout = QHBoxLayout(); top_layout.addWidget(QLabel(self.tr("Displaying attendance for day:"))); self.date_selector = QDateEdit(calendarPopup=True); self.date_selector.setDate(QDate.currentDate()); top_layout.addWidget(self.date_selector); self.refresh_button = QPushButton(self.tr("🔄 Refresh Now")); top_layout.addWidget(self.refresh_button); top_layout.addStretch(); main_layout.addLayout(top_layout)
        tables_layout = QHBoxLayout()
        checkin_layout = QVBoxLayout(); checkin_layout.addWidget(QLabel(f"<h3>✅ {self.tr('Check-in')}</h3>")); self.checkin_table = QTableWidget(); self.checkin_table.setColumnCount(5); self.checkin_table.setHorizontalHeaderLabels([self.tr("Employee"), self.tr("Check-in Time"), self.tr("Status"), self.tr("Notes"), self.tr("Location")]); self.checkin_table.setSortingEnabled(True); checkin_layout.addWidget(self.checkin_table); self.checkin_export_button = QPushButton(f"💾 {self.tr('Export Check-ins (Excel)')}"); checkin_layout.addWidget(self.checkin_export_button); tables_layout.addLayout(checkin_layout)
        checkout_layout = QVBoxLayout(); checkout_layout.addWidget(QLabel(f"<h3>❌ {self.tr('Check-out')}</h3>")); self.checkout_table = QTableWidget(); self.checkout_table.setColumnCount(4); self.checkout_table.setHorizontalHeaderLabels([self.tr("Employee"), self.tr("Check-out Time"), self.tr("Work Duration (H)"), self.tr("Location")]); self.checkout_table.setSortingEnabled(True); checkout_layout.addWidget(self.checkout_table); self.checkout_export_button = QPushButton(f"💾 {self.tr('Export Check-outs (Excel)')}"); checkout_layout.addWidget(self.checkout_export_button); tables_layout.addLayout(checkout_layout)
        main_layout.addLayout(tables_layout)
        self.tabs.addTab(self.dashboard_tab, f"📊 {self.tr('Daily Attendance Log')}")

        # --- التبويبات العامة ---
        self.employees_widget = EmployeesWidget(user_role=self.user_data['role']); self.tabs.addTab(self.employees_widget, f"👥 {self.tr('Manage Employees')}")
        self.reports_widget = ReportsWidget(); self.tabs.addTab(self.reports_widget, f"📄 {self.tr('Reports')}")
        self.search_widget = SearchWidget(); self.tabs.addTab(self.search_widget, f"🔎 {self.tr('Search Employee')}")

        # --- التبويبات الخاصة بالمدير فقط ---
        if self.user_data['role'] == 'Admin':
            self.users_widget = UsersWidget(); self.tabs.addTab(self.users_widget, f"👤 {self.tr('Manage Users')}")
            
            self.settings_widget = SettingsWidget()
            # ربط الإشارات من واجهة الإعدادات بالمنفذات في هذه النافذة
            self.settings_widget.theme_changed.connect(self.apply_theme)
            self.settings_widget.language_changed.connect(self.change_language)
            self.tabs.addTab(self.settings_widget, f"⚙️ {self.tr('Settings')}")

        self.setCentralWidget(self.tabs)

    def connect_signals(self):
        """يربط إشارات عناصر الواجهة بمنافذها."""
        # الحفاظ على التاريخ المحدد عند إعادة البناء
        current_date = self.date_selector.date() if hasattr(self, 'date_selector') else QDate.currentDate()
        self.date_selector.setDate(current_date)
        
        self.date_selector.dateChanged.connect(self.update_dashboard_table)
        self.refresh_button.clicked.connect(self.update_dashboard_table)
        self.checkin_export_button.clicked.connect(lambda: self.export_table_to_excel(self.checkin_table, self.tr("Check-in Report")))
        self.checkout_export_button.clicked.connect(lambda: self.export_table_to_excel(self.checkout_table, self.tr("Check-out Report")))
    
    # --- دوال المنفذات (Slots) للتغيير الفوري ---
    
    def apply_theme(self, theme_name):
        """يقرأ ملف الثيم الجديد ويطبقه على التطبيق فورًا."""
        try:
            with open(f'assets/themes/{theme_name}.qss', 'r', encoding='utf-8') as f:
                self.app.setStyleSheet(f.read())
            print(f"Theme changed instantly to: {theme_name}")
        except Exception as e:
            print(f"Failed to apply theme instantly: {e}")

    def change_language(self, lang_code):
        """يقوم بتحميل ملف الترجمة الجديد وإعادة بناء الواجهة لتطبيق التغييرات."""
        print(f"Language change requested to: {lang_code}")
        # إزالة المترجم القديم
        self.app.removeTranslator(self.translator)
        
        # تحميل وتثبيت المترجم الجديد
        if self.translator.load(QLocale(lang_code), "", "", "translations"):
            self.app.installTranslator(self.translator)
            # تحديث اتجاه الواجهة
            if lang_code == 'ar':
                self.app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
            else:
                self.app.setLayoutDirection(Qt.LayoutDirection.LeftToRight)
            # إعادة بناء الواجهة بالكامل لتطبيق الترجمة على كل النصوص
            self.rebuild_ui()
        else:
            print(f"Could not load new translation for: {lang_code}")

    # --- دوال الخدمات والبيانات ---

    def start_notifier_service(self):
        """يبدأ خدمة الإشعارات في الخلفية."""
        self.notifier_thread = NotifierThread(self)
        self.notifier_thread.update_signal.connect(self.update_dashboard_table)
        self.notifier_thread.start()





    def update_dashboard_table(self):
        """Fetches data from the database and updates the dashboard tables."""
        print("[Dashboard] Refreshing data...")
        selected_date = self.date_selector.date().toString("yyyy-MM-dd")
        all_records = self.db_manager.get_attendance_by_date(selected_date)
        
        checkin_records = [r for r in all_records if r['type'] == 'Check-In']
        checkout_records = [r for r in all_records if r['type'] == 'Check-Out']
        
        work_start_time_str = self.app_settings.get('work_start_time', '08:30:00')
        late_allowance_minutes = int(self.app_settings.get('late_allowance_minutes', '15'))
        work_start_time = QTime.fromString(work_start_time_str, "HH:mm:ss")

        # --- بداية التصحيح: إعادة تنسيق الحلقات ---
        
        # --- ملء جدول الحضور ---
        self.checkin_table.setRowCount(0)
        self.checkin_table.setRowCount(len(checkin_records))
        for row, record in enumerate(checkin_records):
            # يتم تعريف المتغيرات داخل الحلقة هنا
            arrival_time = QTime.fromString(record['check_time'], "HH:mm:ss")
            time_item = QTableWidgetItem(record['check_time'])
            status_item = QTableWidgetItem(self.tr("On Time"))
            
            # يتم استخدام المتغيرات داخل نفس الحلقة
            if arrival_time > work_start_time.addSecs(late_allowance_minutes * 60):
                time_item.setForeground(QColor('red'))
                status_item.setText(self.tr("Late"))
                status_item.setForeground(QColor('red'))
            
            self.checkin_table.setItem(row, 0, QTableWidgetItem(record['name']))
            self.checkin_table.setItem(row, 1, time_item)
            self.checkin_table.setItem(row, 2, status_item)
            self.checkin_table.setItem(row, 3, QTableWidgetItem(record.get('notes', '')))
            
            lat, lon = record.get('location_lat'), record.get('location_lon')
            if lat and lon:
                map_button = QPushButton(f"🗺️ {self.tr('View')}")
                map_button.clicked.connect(lambda ch, la=lat, lo=lon: self.open_map(la, lo))
                self.checkin_table.setCellWidget(row, 4, map_button)

        # --- ملء جدول الانصراف ---
        self.checkout_table.setRowCount(0)
        self.checkout_table.setRowCount(len(checkout_records))
        for row, record in enumerate(checkout_records):
            self.checkout_table.setItem(row, 0, QTableWidgetItem(record['name']))
            self.checkout_table.setItem(row, 1, QTableWidgetItem(record['check_time']))
            
            duration = record.get('work_duration_hours')
            duration_str = str(duration) if duration is not None else ""
            self.checkout_table.setItem(row, 2, QTableWidgetItem(duration_str))
            
            lat, lon = record.get('location_lat'), record.get('location_lon')
            if lat and lon:
                map_button = QPushButton(f"🗺️ {self.tr('View')}")
                map_button.clicked.connect(lambda ch, la=lat, lo=lon: self.open_map(la, lo))
                self.checkout_table.setCellWidget(row, 3, map_button)
        # --- نهاية التصحيح ---






    def export_table_to_excel(self, table: QTableWidget, report_name: str):
        # ... (نفس كود هذه الدالة بدون تغيير) ...
        if table.rowCount() == 0: QMessageBox.warning(self, self.tr("No Data"), self.tr("There is no data in the table to export.")); return
        file_path, _ = QFileDialog.getSaveFileName(self, self.tr("Save Report"), "", f"{self.tr('Excel Files (*.xlsx)')}");
        if not file_path: return
        try:
            headers = [table.horizontalHeaderItem(i).text() for i in range(table.columnCount())]; data = []
            for row in range(table.rowCount()):
                row_data = {headers[col]: (table.item(row, col).text() if table.item(row, col) else "") for col in range(table.columnCount()) if not table.cellWidget(row, col)}
                data.append(row_data)
            df = pd.DataFrame(data); df.to_excel(file_path, index=False, engine='openpyxl')
            QMessageBox.information(self, self.tr("Success"), f"{self.tr('Report saved successfully at:')}\n{file_path}")
        except Exception as e: QMessageBox.critical(self, self.tr("Error"), f"{self.tr('Failed to save the report:')} {e}")
    
    def open_map(self, lat, lon):
        # ... (نفس كود هذه الدالة بدون تغيير) ...
        url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"; webbrowser.open(url)