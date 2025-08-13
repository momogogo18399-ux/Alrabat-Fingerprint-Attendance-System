import sys
import webbrowser
import pandas as pd
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QApplication, QDateEdit, QHBoxLayout,
    QMessageBox, QFileDialog, QMenuBar, QStatusBar
)
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QDate, QTime, QCoreApplication, QTranslator, QLocale, QTimer

# استيراد جميع الواجهات الفرعية والوحدات الخدمية
from app.gui.employees_widget import EmployeesWidget
from app.gui.reports_widget import ReportsWidget
from app.gui.search_widget import SearchWidget
from app.gui.settings_widget import SettingsWidget
from app.gui.users_widget import UsersWidget
from app.gui.locations_widget import LocationsWidget
from app.database.database_manager import DatabaseManager
from app.utils.notifier import NotifierThread
from app.gui.holidays_widget import HolidaysWidget # <-- استيراد الواجهة الجديدة
from app.utils.app_logger import get_logger
from app.utils.update_checker import get_current_version, fetch_latest_info, is_newer_version, download_file, run_windows_installer


class MainWindow(QMainWindow):
    """
    النافذة الرئيسية للتطبيق، تعمل كلوحة تحكم وحاوية لجميع الواجهات الأخرى.
    """
    def __init__(self, user_data: dict, app_instance):
        super().__init__()
        self.user_data = user_data
        self.db_manager = DatabaseManager()
        self.logger = get_logger("MainWindow")
        self.app = app_instance
        self.translator = QTranslator(self)
        self.app_settings = self.db_manager.get_all_settings()
        
        # تحميل المواقع المعتمدة في ذاكرة مؤقتة لتحسين الأداء
        self.locations_cache = {loc['id']: loc for loc in (self.db_manager.get_all_locations() or [])}
        
        self.initial_load_language()
        self.rebuild_ui()
        self.start_notifier_service()
        self.start_auto_refresh_timer()
        QTimer.singleShot(4000, self.auto_check_updates_on_start)

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
        try:
            from app.utils.resources import resource_path
            self.setWindowIcon(QIcon(resource_path('assets/icons/app.png')))
        except Exception:
            pass
        
        self.setup_ui_elements()
        self.connect_signals()
        
        if hasattr(self, 'date_selector'):
            self.update_dashboard_table()

    def setup_ui_elements(self):
        """
        ينشئ وينظم جميع عناصر واجهة المستخدم والتبويبات.
        """
        # شريط القوائم
        self._ensure_menu_bar()

        # شريط الحالة
        self._ensure_status_bar()

        self.tabs = QTabWidget(); self.tabs.setFont(QFont("Arial", 11))
        
        # --- تبويب لوحة التحكم (Dashboard) ---
        self.dashboard_tab = QWidget()
        main_layout = QVBoxLayout(self.dashboard_tab)
        top_layout = QHBoxLayout(); top_layout.addWidget(QLabel(self.tr("Displaying attendance for day:"))); self.date_selector = QDateEdit(calendarPopup=True); self.date_selector.setDate(QDate.currentDate()); top_layout.addWidget(self.date_selector); self.refresh_button = QPushButton(self.tr("🔄 Refresh Now")); top_layout.addWidget(self.refresh_button); top_layout.addStretch(); main_layout.addLayout(top_layout)
        
        tables_layout = QHBoxLayout()
        
        checkin_layout = QVBoxLayout(); checkin_layout.addWidget(QLabel(f"<h3>✅ {self.tr('Check-in')}</h3>"))
        self.checkin_table = QTableWidget(); self.checkin_table.setColumnCount(6)
        self.checkin_table.setHorizontalHeaderLabels([self.tr("Employee"), self.tr("Check-in Time"), self.tr("Status"), self.tr("Notes"), self.tr("Approved Location"), self.tr("Map View")])
        self.checkin_table.setSortingEnabled(True); checkin_layout.addWidget(self.checkin_table)
        self.checkin_export_button = QPushButton(f"💾 {self.tr('Export Check-ins (Excel)')}"); checkin_layout.addWidget(self.checkin_export_button); tables_layout.addLayout(checkin_layout)
        
        checkout_layout = QVBoxLayout(); checkout_layout.addWidget(QLabel(f"<h3>❌ {self.tr('Check-out')}</h3>"))
        self.checkout_table = QTableWidget(); self.checkout_table.setColumnCount(5)
        self.checkout_table.setHorizontalHeaderLabels([self.tr("Employee"), self.tr("Check-out Time"), self.tr("Work Duration (H)"), self.tr("Approved Location"), self.tr("Map View")])
        self.checkout_table.setSortingEnabled(True); checkout_layout.addWidget(self.checkout_table)
        self.checkout_export_button = QPushButton(f"💾 {self.tr('Export Check-outs (Excel)')}"); checkout_layout.addWidget(self.checkout_export_button); tables_layout.addLayout(checkout_layout)
        
        main_layout.addLayout(tables_layout)
        self.tabs.addTab(self.dashboard_tab, f"📊 {self.tr('Daily Attendance Log')}")

        # --- التبويبات العامة ---
        self.employees_widget = EmployeesWidget(user_role=self.user_data['role']); self.tabs.addTab(self.employees_widget, f"👥 {self.tr('Manage Employees')}")
        self.reports_widget = ReportsWidget(); self.tabs.addTab(self.reports_widget, f"📄 {self.tr('Reports')}")
        self.search_widget = SearchWidget(); self.tabs.addTab(self.search_widget, f"🔎 {self.tr('Search Employee')}")

        # --- التبويبات الخاصة بالمدير فقط ---
        if self.user_data['role'] == 'Admin':
            self.locations_widget = LocationsWidget()
            self.tabs.addTab(self.locations_widget, f"📍 {self.tr('Manage Locations')}")
            self.holidays_widget = HolidaysWidget() # <-- إنشاء نسخة
            self.tabs.addTab(self.holidays_widget, f"📅 {self.tr('Manage Holidays')}") # <-- إضافة التبويب

            self.users_widget = UsersWidget()
            self.tabs.addTab(self.users_widget, f"👤 {self.tr('Manage Users')}")
            
            self.settings_widget = SettingsWidget()
            self.settings_widget.theme_changed.connect(self.apply_theme)
            self.settings_widget.language_changed.connect(self.change_language)
            self.tabs.addTab(self.settings_widget, f"⚙️ {self.tr('Settings')}")

        self.setCentralWidget(self.tabs)

        # تحديث شريط الحالة بمعلومات المستخدم
        if self.statusBar():
            self.statusBar().showMessage(self.tr("Logged in as") + f": {self.user_data.get('username')} ({self.user_data.get('role')})")

    def connect_signals(self):
        self.date_selector.dateChanged.connect(self.update_dashboard_table)
        self.refresh_button.clicked.connect(self.update_dashboard_table)
        self.checkin_export_button.clicked.connect(lambda: self.export_table_to_excel(self.checkin_table, self.tr("Check-in Report")))
        self.checkout_export_button.clicked.connect(lambda: self.export_table_to_excel(self.checkout_table, self.tr("Check-out Report")))
    
    def apply_theme(self, theme_name):
        try:
            import os
            from app.utils.resources import resource_path
            theme_dir = resource_path('assets/themes')
            with open(os.path.join(theme_dir, f'{theme_name}.qss'), 'r', encoding='utf-8') as f:
                self.app.setStyleSheet(f.read())
        except Exception as e: print(f"Failed to apply theme: {e}")

    def change_language(self, lang_code):
        self.app.removeTranslator(self.translator)
        if self.translator.load(QLocale(lang_code), "", "", "translations"):
            self.app.installTranslator(self.translator)
            self.app.setLayoutDirection(Qt.LayoutDirection.RightToLeft if lang_code == 'ar' else Qt.LayoutDirection.LeftToRight)
            self.rebuild_ui()
        else: print(f"Could not load new translation for: {lang_code}")

    def start_notifier_service(self):
        self.notifier_thread = NotifierThread(self)
        self.notifier_thread.update_signal.connect(self.update_dashboard_table)
        self.notifier_thread.start()
        self.logger.info("Notifier service started")

    def stop_notifier_service(self):
        if hasattr(self, 'notifier_thread') and self.notifier_thread is not None:
            try:
                self.notifier_thread.update_signal.disconnect(self.update_dashboard_table)
            except Exception:
                pass
            self.notifier_thread.stop()
            self.notifier_thread.quit()
            self.notifier_thread.wait(2000)

    def update_dashboard_table(self):
        """
        يجلب البيانات ويحدّث جداول لوحة التحكم، مع منطق صحيح لزر الخريطة.
        """
        print("[Dashboard] Refreshing data...")
        self.locations_cache = {loc['id']: loc for loc in (self.db_manager.get_all_locations() or [])}
        
        selected_date = self.date_selector.date().toString("yyyy-MM-dd")
        all_records = self.db_manager.get_attendance_by_date(selected_date) or []
        
        checkin_records = [r for r in all_records if r['type'] == 'Check-In']
        checkout_records = [r for r in all_records if r['type'] == 'Check-Out']
        
        work_start_time_str = self.app_settings.get('work_start_time', '08:30:00')
        late_allowance_minutes = int(self.app_settings.get('late_allowance_minutes', '15'))
        work_start_time = QTime.fromString(work_start_time_str, "HH:mm:ss")

        # ملء جدول الحضور
        self.checkin_table.setRowCount(0)
        self.checkin_table.setRowCount(len(checkin_records))
        for row, record in enumerate(checkin_records):
            arrival_time = QTime.fromString(record['check_time'], "HH:mm:ss")
            time_item = QTableWidgetItem(record['check_time'])
            status_item = QTableWidgetItem(self.tr("On Time"))
            if arrival_time > work_start_time.addSecs(late_allowance_minutes * 60):
                time_item.setForeground(QColor('red')); status_item.setText(self.tr("Late")); status_item.setForeground(QColor('red'))
            
            self.checkin_table.setItem(row, 0, QTableWidgetItem(record['employee_name']))
            self.checkin_table.setItem(row, 1, time_item)
            self.checkin_table.setItem(row, 2, status_item)
            self.checkin_table.setItem(row, 3, QTableWidgetItem(record.get('notes', '')))
            
            location_id = record.get('location_id')
            location_name = record.get('location_name', self.tr('N/A'))
            self.checkin_table.setItem(row, 4, QTableWidgetItem(location_name))
            
            # الآن هذا الشرط سيعمل بشكل صحيح
            if location_id and location_id in self.locations_cache:
                location_info = self.locations_cache[location_id]
                lat, lon = location_info['latitude'], location_info['longitude']
                map_button = QPushButton(f"🗺️ {self.tr('View')}")
                map_button.clicked.connect(lambda ch, la=lat, lo=lon: self.open_map(la, lo))
                self.checkin_table.setCellWidget(row, 5, map_button)

        # ملء جدول الانصراف
        self.checkout_table.setRowCount(0)
        self.checkout_table.setRowCount(len(checkout_records))
        for row, record in enumerate(checkout_records):
            self.checkout_table.setItem(row, 0, QTableWidgetItem(record['employee_name']))
            self.checkout_table.setItem(row, 1, QTableWidgetItem(record['check_time']))
            duration = record.get('work_duration_hours'); duration_str = str(duration) if duration is not None else ""; 
            self.checkout_table.setItem(row, 2, QTableWidgetItem(duration_str))
            
            location_id = record.get('location_id')
            location_name = record.get('location_name', self.tr('N/A'))
            self.checkout_table.setItem(row, 3, QTableWidgetItem(location_name))
            
            if location_id and location_id in self.locations_cache:
                location_info = self.locations_cache[location_id]
                lat, lon = location_info['latitude'], location_info['longitude']
                map_button = QPushButton(f"🗺️ {self.tr('View')}")
                map_button.clicked.connect(lambda ch, la=lat, lo=lon: self.open_map(la, lo))
                self.checkout_table.setCellWidget(row, 4, map_button)



    def export_table_to_excel(self, table: QTableWidget, report_name: str):
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
        url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"; webbrowser.open(url)

    # --- عناصر القوائم وشريط الحالة ---
    def _ensure_menu_bar(self):
        menubar: QMenuBar = self.menuBar() or QMenuBar(self)
        self.setMenuBar(menubar)

        file_menu = menubar.addMenu(self.tr("File"))

        logout_action = QAction(self.tr("Logout"), self)
        logout_action.triggered.connect(self._handle_logout)
        file_menu.addAction(logout_action)

        exit_action = QAction(self.tr("Exit"), self)
        exit_action.triggered.connect(self._handle_exit)
        file_menu.addAction(exit_action)

        help_menu = menubar.addMenu(self.tr("Help"))
        about_action = QAction(self.tr("About"), self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        check_updates_action = QAction(self.tr("Check for Updates"), self)
        check_updates_action.triggered.connect(self._check_for_updates_clicked)
        help_menu.addAction(check_updates_action)

    def _ensure_status_bar(self):
        if not self.statusBar():
            self.setStatusBar(QStatusBar(self))

    def _handle_logout(self):
        from app.login_window import LoginWindow
        confirm = QMessageBox.question(self, self.tr("Confirm"), self.tr("Do you want to logout?"))
        if confirm == QMessageBox.StandardButton.Yes:
            self.stop_notifier_service()
            self.close()
            login = LoginWindow()
            login.show()

    def _handle_exit(self):
        confirm = QMessageBox.question(self, self.tr("Confirm"), self.tr("Exit the application?"))
        if confirm == QMessageBox.StandardButton.Yes:
            self.stop_notifier_service()
            QApplication.instance().quit()

    def _show_about(self):
        current_version = get_current_version()
        QMessageBox.information(self, self.tr("About"), self.tr("Employee Attendance System") + f"\n{self.tr('Version')}: {current_version}\n\n" + self.tr("Developed with Python, PyQt6, and Flask."))

    def closeEvent(self, event):
        # ضمان إيقاف الخيوط الخلفية قبل الغلق
        self.stop_notifier_service()
        super().closeEvent(event)

    def start_auto_refresh_timer(self):
        """
        مؤقت تحديث دوري خفيف لتحديث لوحة التحكم تلقائيًا.
        الافتراضي 15 ثانية ويمكن تعديل الفترة لاحقًا من الإعدادات.
        """
        try:
            interval_seconds = int(self.app_settings.get('dashboard_refresh_seconds', '15'))
        except Exception:
            interval_seconds = 15
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.update_dashboard_table)
        self.auto_refresh_timer.start(max(5, interval_seconds) * 1000)
        self.logger.info(f"Auto-refresh timer started: every {max(5, interval_seconds)}s")

    # --- تحديثات التطبيق ---
    def _check_for_updates_clicked(self):
        self.perform_update_check(interactive=True)

    def auto_check_updates_on_start(self):
        try:
            auto_check = True
            if auto_check:
                self.perform_update_check(interactive=False)
        except Exception as e:
            self.logger.error(f"Auto update check failed: {e}")

    def perform_update_check(self, interactive: bool = False):
        try:
            current = get_current_version()
            latest_info = fetch_latest_info()
            if not latest_info:
                if interactive:
                    QMessageBox.information(self, self.tr("Updates"), self.tr("Could not reach update server."))
                return

            latest_version = latest_info.get('version', '0.0.0')
            notes = latest_info.get('notes', '')
            mandatory = bool(latest_info.get('mandatory', False))
            download_url = latest_info.get('download_url')

            if not is_newer_version(latest_version, current):
                if interactive:
                    QMessageBox.information(self, self.tr("Updates"), self.tr("You are on the latest version."))
                return

            msg = self.tr("A new version is available") + f" ({latest_version}).\n\n" + notes
            buttons = QMessageBox.StandardButton.Ok if mandatory else (QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            default = QMessageBox.StandardButton.Ok if mandatory else QMessageBox.StandardButton.Yes
            reply = QMessageBox.information(self, self.tr("Update Available"), msg, buttons, default)

            if mandatory and download_url:
                self._download_and_install(download_url)
                return

            if not mandatory and reply == QMessageBox.StandardButton.Yes and download_url:
                self._download_and_install(download_url)
        except Exception as e:
            if interactive:
                QMessageBox.warning(self, self.tr("Updates"), f"{self.tr('Update check failed')}: {e}")
            self.logger.error(f"Update check error: {e}")

    def _download_and_install(self, url: str):
        try:
            self.statusBar().showMessage(self.tr("Downloading update..."))
            local_path = download_file(url)
            if not local_path:
                QMessageBox.critical(self, self.tr("Updates"), self.tr("Failed to download the update."))
                return
            ok = run_windows_installer(local_path, silent=True)
            if ok:
                QMessageBox.information(self, self.tr("Updates"), self.tr("Installer started. The application may close or restart during update."))
            else:
                QMessageBox.warning(self, self.tr("Updates"), self.tr("Could not start installer automatically. Please run it manually."))
        except Exception as e:
            QMessageBox.critical(self, self.tr("Updates"), f"{self.tr('Update failed')}: {e}")
        finally:
            self.statusBar().clearMessage()