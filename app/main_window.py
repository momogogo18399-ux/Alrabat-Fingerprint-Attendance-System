import sys
import webbrowser
import pandas as pd
from PyQt6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QLabel, QTableWidget, 
    QTableWidgetItem, QHeaderView, QPushButton, QApplication, QDateEdit, QHBoxLayout,
    QMessageBox, QFileDialog, QMenuBar, QStatusBar
)
from PyQt6.QtGui import QAction, QIcon, QPixmap
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, QDate, QTime, QCoreApplication, QTranslator, QLocale, QTimer

# استيراد جميع الواجهات الفرعية والوحدات الخدمية
from app.gui.employees_widget import EmployeesWidget
from app.gui.reports_widget import ReportsWidget
from app.gui.search_widget import SearchWidget
from app.gui.settings_widget import SettingsWidget
from app.gui.users_widget import UsersWidget
from app.gui.locations_widget import LocationsWidget
from app.database.simple_hybrid_manager import SimpleHybridManager
from app.utils.notifier import NotifierThread
from app.gui.holidays_widget import HolidaysWidget # <-- استيراد الواجهة الجديدة
from app.gui.gentle_notification import GentleNotification  # <-- استيراد الإشعارات اللطيفة
from app.utils.app_logger import get_logger
from app.utils.update_checker import get_current_version, fetch_latest_info, is_newer_version, download_file, run_windows_installer
from app.core.notifications_manager import NotificationsManager  # <-- استيراد مدير التنبيهات المتقدم
from datetime import datetime


class MainWindow(QMainWindow):
    """
    النافذة الرئيسية للتطبيق، تعمل كلوحة تحكم وحاوية لجميع الواجهات الأخرى.
    """
    def __init__(self, user_data: dict, app_instance, db_manager=None):
        super().__init__()
        self.user_data = user_data
        self.db_manager = db_manager or SimpleHybridManager()
        self.logger = get_logger("MainWindow")
        self.app = app_instance
        self.translator = QTranslator(self)
        self.app_settings = self.db_manager.get_all_settings()
        
        # تحميل المواقع المعتمدة في ذاكرة مؤقتة لتحسين الأداء
        self.locations_cache = {loc['id']: loc for loc in (self.db_manager.get_all_locations() or [])}
        
        # نظام التنبيهات المشترك
        self.shared_notifications = []
        
        # تهيئة مدير التنبيهات المتقدم
        try:
            import os
            # Try both naming conventions for Supabase credentials
            supabase_url = os.getenv('SUPABASE_URL') or os.getenv('NEXT_PUBLIC_SUPABASE_URL', '')
            supabase_key = os.getenv('SUPABASE_KEY') or os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY', '')
            
            if supabase_url and supabase_key:
                self.notifications_manager = NotificationsManager(supabase_url, supabase_key)
                self.logger.info("✅ Advanced Notifications Manager initialized successfully")
            else:
                self.logger.warning("⚠️ Supabase credentials not found, notifications will use local mode")
                self.notifications_manager = None
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize Notifications Manager: {e}")
            self.notifications_manager = None
        
        self.initial_load_language()
        self.rebuild_ui()
        self.start_notifier_service()
        self.start_auto_refresh_timer()
        self.start_change_detection_system()  # 🆕 نظام كشف التغييرات
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
            import os
            from app.utils.resources import resource_path
            rabat_logo = resource_path('assets/icons/rabat-logo.jpg')
            if os.path.exists(rabat_logo):
                self.setWindowIcon(QIcon(rabat_logo))
            else:
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

        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        self.tabs.setTabPosition(QTabWidget.TabPosition.North)
        self.tabs.setMovable(True)
        self.tabs.setTabsClosable(False)
        self.tabs.setUsesScrollButtons(True)
        
        # تطبيق تنسيق جميل للتبويبات
        self.apply_tab_styling()
        
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
        self.tabs.addTab(self.dashboard_tab, f"📊 {self.tr('Dashboard')}")

        # --- التبويبات العامة ---
        self.employees_widget = EmployeesWidget(user_role=self.user_data['role'], db_manager=self.db_manager)
        self.tabs.addTab(self.employees_widget, f"👥 {self.tr('Employees')}")
        self.reports_widget = ReportsWidget(db_manager=self.db_manager)
        self.tabs.addTab(self.reports_widget, f"📊 {self.tr('Reports')}")
        self.search_widget = SearchWidget(db_manager=self.db_manager)
        self.tabs.addTab(self.search_widget, f"🔍 {self.tr('Search')}")

        # --- التبويبات الخاصة بالمدير فقط ---
        if self.user_data['role'] == 'Admin':
            self.locations_widget = LocationsWidget(db_manager=self.db_manager)
            self.tabs.addTab(self.locations_widget, f"📍 {self.tr('Locations')}")
            self.holidays_widget = HolidaysWidget(db_manager=self.db_manager)
            self.tabs.addTab(self.holidays_widget, f"📅 {self.tr('Holidays')}")

            self.users_widget = UsersWidget(db_manager=self.db_manager)
            self.tabs.addTab(self.users_widget, f"👤 {self.tr('Users')}")
            
            self.settings_widget = SettingsWidget()
            self.settings_widget.theme_changed.connect(self.apply_theme)
            self.settings_widget.language_changed.connect(self.change_language)
            self.tabs.addTab(self.settings_widget, f"⚙️ {self.tr('Settings')}")

        # --- تبويبات الذكاء الاصطناعي الجديدة ---
        self.setup_ai_tabs()
        
        # --- تبويب التنبيهات ---
        self.setup_notifications_tab()

        self.setCentralWidget(self.tabs)

        # Update شريط الحالة بInformation المستخدم
        if self.statusBar():
            self.statusBar().showMessage(self.tr("Logged in as") + f": {self.user_data.get('username')} ({self.user_data.get('role')})")

    def connect_signals(self):
        self.date_selector.dateChanged.connect(self.update_dashboard_table)
        self.refresh_button.clicked.connect(self.update_dashboard_table)
        self.checkin_export_button.clicked.connect(lambda: self.export_table_to_excel(self.checkin_table, self.tr("Check-in Report")))
        self.checkout_export_button.clicked.connect(lambda: self.export_table_to_excel(self.checkout_table, self.tr("Check-out Report")))
    
    def apply_theme(self, theme_name):
        """تطبيق الثيم الجديد على التطبيق"""
        try:
            import os
            from app.utils.resources import resource_path
            
            # الحصول على مسار الثيم
            theme_dir = resource_path('assets/themes')
            theme_file = os.path.join(theme_dir, f'{theme_name}.qss')
            
            # التحقق من وجود ملف الثيم
            if not os.path.exists(theme_file):
                print(f"Theme file not found: {theme_file}")
                return
            
            # قراءة وتطبيق الثيم
            with open(theme_file, 'r', encoding='utf-8') as f:
                stylesheet = f.read()
                
            # تطبيق الثيم على التطبيق الرئيسي
            if hasattr(self, 'app') and self.app:
                self.app.setStyleSheet(stylesheet)
                print(f"✅ تم تطبيق الثيم: {theme_name}")
            else:
                # إذا لم يكن app متاحاً، استخدم QApplication.instance()
                from PyQt6.QtWidgets import QApplication
                app = QApplication.instance()
                if app:
                    app.setStyleSheet(stylesheet)
                    print(f"✅ تم تطبيق الثيم: {theme_name}")
                else:
                    print("❌ لا يمكن العثور على تطبيق PyQt")
                    
        except Exception as e:
            print(f"❌ Failed في تطبيق الثيم {theme_name}: {e}")
            import traceback
            traceback.print_exc()

    def change_language(self, lang_code):
        self.app.removeTranslator(self.translator)
        if self.translator.load(QLocale(lang_code), "", "", "translations"):
            self.app.installTranslator(self.translator)
            self.app.setLayoutDirection(Qt.LayoutDirection.RightToLeft if lang_code == 'ar' else Qt.LayoutDirection.LeftToRight)
    
    def setup_ai_tabs(self):
        """إعداد تبويبات الذكاء الاصطناعي الجديدة"""
        try:
            # استيراد الواجهات الجديدة
            from app.gui.ai_assistant_widget import AIAssistantWidget
            from app.gui.advanced_analytics_widget import AdvancedAnalyticsWidget
            
            # تبويب المساعد الذكي
            self.ai_assistant_widget = AIAssistantWidget(self.db_manager)
            self.tabs.addTab(self.ai_assistant_widget, f"🤖 {self.tr('AI Assistant')}")
            
            # تبويب التحليل المتقدم
            self.advanced_analytics_widget = AdvancedAnalyticsWidget(self.db_manager)
            self.tabs.addTab(self.advanced_analytics_widget, f"📈 {self.tr('Analytics')}")
            
            print("✅ تم Add تبويبات الذكاء الاصطناعي بنجاح")
            
        except Exception as e:
            print(f"❌ Failed في Add تبويبات الذكاء الاصطناعي: {e}")
            import traceback
            traceback.print_exc()
            self.rebuild_ui()
        # تم Add تبويبات الذكاء الاصطناعي بنجاح

    def setup_notifications_tab(self):
        """إعداد تبويب التنبيهات - تصميم جديد ومحسن"""
        try:
            # استيراد واجهات التنبيهات
            from app.gui.admin_notifications_widget import AdminNotificationsWidget
            from app.gui.user_notifications_widget import UserNotificationsWidget
            
            # الحصول على بيانات Supabase من البيئة
            import os
            supabase_url = os.getenv('SUPABASE_URL') or os.getenv('NEXT_PUBLIC_SUPABASE_URL', '')
            supabase_key = os.getenv('SUPABASE_KEY') or os.getenv('NEXT_PUBLIC_SUPABASE_ANON_KEY', '')
            
            if self.user_data['role'] == 'Admin':
                # تبويب إرسال التنبيهات للمدير - تصميم جديد
                try:
                    self.admin_notifications_widget = AdminNotificationsWidget(
                        self.db_manager,
                        supabase_url=supabase_url,
                        supabase_key=supabase_key
                    )
                    # Ensure the widget has a proper parent
                    self.admin_notifications_widget.setParent(self.tabs)
                    self.tabs.addTab(self.admin_notifications_widget, f"🔔 {self.tr('Notifications')}")
                    
                    # ربط إشارة إرسال التنبيه
                    self.admin_notifications_widget.notification_sent.connect(self.on_admin_notification_sent)
                    
                    # ربط إشارة إضافة التنبيه للتحديث المباشر
                    self.admin_notifications_widget.notification_added.connect(self.on_notification_added)
                    
                    print("✅ تم إنشاء Admin Notifications Widget الجديد بنجاح")
                    
                except Exception as widget_error:
                    print(f"❌ Failed في إنشاء Admin Notifications Widget: {widget_error}")
                    import traceback
                    traceback.print_exc()
                    # Create a fallback widget
                    fallback_widget = QWidget()
                    fallback_layout = QVBoxLayout()
                    fallback_label = QLabel("Failed to load Admin Notifications Widget")
                    fallback_layout.addWidget(fallback_label)
                    fallback_widget.setLayout(fallback_layout)
                    self.tabs.addTab(fallback_widget, "🔔 Admin Notifications (Error)")
                
            else:
                # تبويب عرض التنبيهات للمستخدمين العاديين
                try:
                    self.user_notifications_widget = UserNotificationsWidget(
                        self.db_manager, 
                        self.user_data.get('id'), 
                        self.user_data.get('role'),
                        supabase_url=supabase_url,
                        supabase_key=supabase_key
                    )
                    # Ensure the widget has a proper parent
                    self.user_notifications_widget.setParent(self.tabs)
                    self.tabs.addTab(self.user_notifications_widget, f"🔔 {self.tr('Notifications')}")
                    print("✅ تم إنشاء User Notifications Widget بنجاح")
                    
                except Exception as widget_error:
                    print(f"❌ Failed في إنشاء User Notifications Widget: {widget_error}")
                    import traceback
                    traceback.print_exc()
                    # Create a fallback widget
                    fallback_widget = QWidget()
                    fallback_layout = QVBoxLayout()
                    fallback_label = QLabel("Failed to load User Notifications Widget")
                    fallback_layout.addWidget(fallback_label)
                    fallback_widget.setLayout(fallback_layout)
                    self.tabs.addTab(fallback_widget, "🔔 Notifications (Error)")
            
            print("✅ تم Add تبويب التنبيهات بنجاح")
            
        except Exception as e:
            print(f"❌ Failed في Add تبويب التنبيهات: {e}")
            import traceback
            traceback.print_exc()
            # Create a basic error tab
            error_widget = QWidget()
            error_layout = QVBoxLayout()
            error_label = QLabel("Failed to load Notifications System")
            error_layout.addWidget(error_label)
            error_widget.setLayout(error_layout)
            self.tabs.addTab(error_widget, "🔔 Notifications (System Error)")

    def on_notification_added(self, notification_data: dict):
        """معالج إضافة تنبيه جديد للتحديث المباشر (للتوافق مع النظام القديم)"""
        try:
            print(f"🔔 New notification added: {notification_data.get('title', 'Unknown')}")
            
            # في النظام الجديد، التحديثات تتم تلقائياً عبر مدير التنبيهات
            # هذا المعالج موجود للتوافق مع النظام القديم
            if hasattr(self, 'notifications_manager') and self.notifications_manager:
                print(f"✅ التنبيه تم إرساله عبر مدير التنبيهات المتقدم")
            else:
                print("⚠️ مدير التنبيهات المتقدم غير متاح")
                
        except Exception as e:
            print(f"❌ Failed في معالجة إضافة التنبيه الجديد: {e}")
            import traceback
            traceback.print_exc()

    def add_shared_notification(self, notification_data: dict):
        """إضافة تنبيه مشترك لجميع المستخدمين"""
        try:
            # إضافة معرف فريد
            notification_data['id'] = str(len(self.shared_notifications) + 1)
            notification_data['timestamp'] = datetime.now().isoformat()
            notification_data['status'] = 'unread'
            
            # إضافة للقائمة المشتركة
            self.shared_notifications.append(notification_data)
            
            # إرسال التنبيه لجميع المستخدمين المفتوحين
            if hasattr(self, 'user_notifications_widget'):
                self.user_notifications_widget.add_notification(notification_data.copy())
            
            print(f"✅ تم إضافة التنبيه المشترك: {notification_data['title']}")
            return True
            
        except Exception as e:
            print(f"❌ Failed في إضافة التنبيه المشترك: {e}")
            import traceback
            traceback.print_exc()
            return False

    def get_shared_notifications(self):
        """الحصول على جميع التنبيهات المشتركة"""
        return self.shared_notifications.copy()
    
    def get_current_user_info(self):
        """الحصول على معلومات المستخدم الحالي للتنبيهات"""
        return {
            'id': self.user_data.get('id', ''),
            'username': self.user_data.get('username', ''),
            'role': self.user_data.get('role', ''),
            'email': self.user_data.get('email', '')
        }



    def on_admin_notification_sent(self, notification_type: str, message: str):
        """معالج إرسال التنبيه من المدير - تصميم جديد"""
        try:
            print(f"🔔 Admin notification sent: {notification_type} - {message}")
            
            # إنشاء بيانات التنبيه المتقدمة
            notification_data = {
                "notification_type": notification_type,
                "priority": "medium",
                "title": f"Admin Notification - {datetime.now().strftime('%H:%M')}",
                "message": message,
                "admin_id": self.user_data.get('id', 'admin'),
                "admin_name": self.user_data.get('username', 'Admin'),
                "target_users": "all",
                "target_user_ids": [],  # Empty for all users
                "status": "active",
                "tags": ["admin", "system"],
                "metadata": {
                    "source": "main_window",
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            # إرسال التنبيه عبر مدير التنبيهات المتقدم
            if hasattr(self, 'notifications_manager') and self.notifications_manager:
                success = self.notifications_manager.send_notification(notification_data)
                if success:
                    print(f"✅ تم إرسال التنبيه عبر مدير التنبيهات المتقدم: {notification_data['title']}")
                    
                    # عرض رسالة تأكيد
                    QMessageBox.information(
                        self, 
                        "Notification Sent", 
                        f"Notification sent successfully!\n\nType: {notification_type}\nMessage: {message}"
                    )
                else:
                    print("❌ Failed في إرسال التنبيه عبر مدير التنبيهات")
                    QMessageBox.warning(
                        self,
                        "Warning",
                        "Failed to send notification through advanced system."
                    )
            else:
                print("⚠️ مدير التنبيهات المتقدم غير متاح")
                QMessageBox.warning(
                    self,
                    "Warning",
                    "Advanced notification system is not available."
                )
            
        except Exception as e:
            print(f"❌ Failed في معالجة إرسال التنبيه: {e}")
            import traceback
            traceback.print_exc()

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

        # Add قائمة QR Scanner
        qr_menu = self.menuBar().addMenu("🔍 QR Scanner")
        qr_scanner_action = QAction("Scan QR Codes", self)
        qr_scanner_action.triggered.connect(self._open_qr_scanner)
        qr_menu.addAction(qr_scanner_action)
        
        # Add قائمة إعدادات QR
        qr_settings_action = QAction("⚙️ QR Code Settings", self)
        qr_settings_action.triggered.connect(self._open_qr_settings)
        qr_menu.addAction(qr_settings_action)
        
        # Add قائمة الأدوات المتقدمة
        advanced_qr_action = QAction("🚀 Advanced QR Tools", self)
        advanced_qr_action.setToolTip("Professional QR code generation and management tools")
        advanced_qr_action.triggered.connect(self._open_advanced_qr_tools)
        qr_menu.addAction(advanced_qr_action)

        help_menu = menubar.addMenu(self.tr("Help"))
        
        # User Manual
        user_manual_action = QAction("📖 User Manual", self)
        user_manual_action.setShortcut("F1")
        user_manual_action.setStatusTip("Open user manual and documentation")
        user_manual_action.triggered.connect(self._show_user_manual)
        help_menu.addAction(user_manual_action)
        
        # Quick Start Guide
        quick_start_action = QAction("🚀 Quick Start Guide", self)
        quick_start_action.setStatusTip("Learn how to use the system quickly")
        quick_start_action.triggered.connect(self._show_quick_start_guide)
        help_menu.addAction(quick_start_action)
        
        help_menu.addSeparator()
        
        # Keyboard Shortcuts
        shortcuts_action = QAction("⌨️ Keyboard Shortcuts", self)
        shortcuts_action.setStatusTip("View all available keyboard shortcuts")
        shortcuts_action.triggered.connect(self._show_keyboard_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        # System Information
        system_info_action = QAction("💻 System Information", self)
        system_info_action.setStatusTip("View system information and status")
        system_info_action.triggered.connect(self._show_system_information)
        help_menu.addAction(system_info_action)
        
        help_menu.addSeparator()
        
        # Check for Updates
        check_updates_action = QAction("🔄 Check for Updates", self)
        check_updates_action.setStatusTip("Check for application updates")
        check_updates_action.triggered.connect(self._check_for_updates_clicked)
        help_menu.addAction(check_updates_action)
        
        # Support & Contact
        support_action = QAction("📞 Support & Contact", self)
        support_action.setStatusTip("Get help and contact support")
        support_action.triggered.connect(self._show_support_contact)
        help_menu.addAction(support_action)
        
        help_menu.addSeparator()
        
        # About
        about_action = QAction("ℹ️ About", self)
        about_action.setStatusTip("About the application")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
        
        # 🆕 Add Smart Update Button at the top
        sync_menu = menubar.addMenu("🔄 Sync")
        
        # Smart Update Button
        self.smart_refresh_action = QAction("🔄 Update Data", self)
        self.smart_refresh_action.setToolTip("Update data from shared database")
        self.smart_refresh_action.setStatusTip("Click to update all data from Supabase")
        self.smart_refresh_action.triggered.connect(self.smart_refresh_data)
        sync_menu.addAction(self.smart_refresh_action)
        
        # Change Indicator with Counter
        self.change_indicator_action = QAction("🔴🔄 New Updates", self)
        self.change_indicator_action.setToolTip("New updates available in shared database")
        self.change_indicator_action.setStatusTip("Click to view update details")
        self.change_indicator_action.triggered.connect(self.show_change_notification)
        self.change_indicator_action.setVisible(False)
        sync_menu.addAction(self.change_indicator_action)
        
        # Change Counter (red dot with number)
        self.change_counter_action = QAction("", self)
        self.change_counter_action.setToolTip("Number of new changes")
        self.change_counter_action.setStatusTip("Click to view update details")
        self.change_counter_action.triggered.connect(self.show_change_notification)
        self.change_counter_action.setVisible(False)
        sync_menu.addAction(self.change_counter_action)
        
        # Separator
        sync_menu.addSeparator()
        
        # Sync Information
        sync_info_action = QAction("📊 Sync Information", self)
        sync_info_action.setToolTip("Display sync status information")
        sync_info_action.triggered.connect(self.show_sync_info)
        sync_menu.addAction(sync_info_action)
        
        # Manual Change Check
        manual_check_action = QAction("🔍 Check Changes Now", self)
        manual_check_action.setToolTip("Manually check for changes")
        manual_check_action.triggered.connect(self.manual_check_changes)
        sync_menu.addAction(manual_check_action)
        
        # Separator
        sync_menu.addSeparator()
        
        # Notification Settings
        self.notifications_enabled = True
        self.toggle_notifications_action = QAction("🔕 Disable Notifications", self)
        self.toggle_notifications_action.setToolTip("Enable/Disable automatic notifications")
        self.toggle_notifications_action.triggered.connect(self.toggle_notifications)
        sync_menu.addAction(self.toggle_notifications_action)

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

    def _show_user_manual(self):
        """Show comprehensive user manual"""
        manual_text = """
📖 EMPLOYEE ATTENDANCE SYSTEM - USER MANUAL

🎯 SYSTEM OVERVIEW:
This is a comprehensive attendance management system designed for Rabat Foundation.
It provides real-time attendance tracking, employee management, and detailed reporting.

📋 MAIN FEATURES:

1. 📊 DASHBOARD:
   • Daily attendance overview
   • Check-in/Check-out tracking
   • Real-time data updates
   • Export to Excel functionality

2. 👥 EMPLOYEE MANAGEMENT:
   • Add/Edit/Delete employees
   • Employee information management
   • QR code generation for each employee
   • Bulk import/export capabilities

3. 📄 REPORTS:
   • Attendance reports by date range
   • Employee performance reports
   • Custom report generation
   • Excel export functionality

4. 🔍 SEARCH & FILTER:
   • Search employees by name, ID, or department
   • Advanced filtering options
   • Quick access to employee records

5. 📍 LOCATION MANAGEMENT:
   • Multiple office locations
   • GPS-based attendance tracking
   • Location-based reporting

6. 📅 HOLIDAY MANAGEMENT:
   • Company holiday calendar
   • Holiday-based attendance calculations
   • Custom holiday settings

7. 👤 USER MANAGEMENT:
   • Admin and regular user roles
   • User permissions and access control
   • Secure login system

8. ⚙️ SETTINGS:
   • System configuration
   • Theme and language settings
   • Database synchronization options

9. 🔄 SYNC & UPDATES:
   • Real-time Supabase synchronization
   • Automatic data backup
   • Update notifications

10. 🔔 NOTIFICATIONS:
    • System notifications
    • Admin announcements
    • Update alerts

⌨️ KEYBOARD SHORTCUTS:
• F1 - User Manual
• F2 - Scan QR Code
• F3 - Manual Entry
• F5 - Record Attendance
• F6 - View Attendance
• F7 - Attendance History
• F12 - Sync Now
• Ctrl+E - Add Employee
• Ctrl+F - Search Employee
• Ctrl+R - Generate Reports
• Ctrl+S - Save Settings
• Ctrl+Q - Exit Application

🔧 SYSTEM REQUIREMENTS:
• Windows 10/11
• Python 3.8+
• Internet connection for sync
• Minimum 4GB RAM
• 500MB free disk space

📞 SUPPORT:
For technical support or questions, contact:
• Email: support@rabatfoundation.org
• Phone: +20-XXX-XXXX-XXX
• Office: Rabat Foundation IT Department

🔄 UPDATES:
The system automatically checks for updates.
You can manually check using Help > Check for Updates.

📚 ADDITIONAL RESOURCES:
• Quick Start Guide: Help > Quick Start Guide
• Keyboard Shortcuts: Help > Keyboard Shortcuts
• System Information: Help > System Information
        """
        
        self._show_help_dialog("📖 User Manual", manual_text)

    def _show_quick_start_guide(self):
        """Show quick start guide"""
        guide_text = """
🚀 QUICK START GUIDE

Welcome to the Employee Attendance System! Follow these steps to get started:

📋 STEP 1: INITIAL SETUP
1. Login with your admin credentials
2. Go to Settings tab to configure system preferences
3. Set your work hours and late allowance
4. Configure your company information

👥 STEP 2: ADD EMPLOYEES
1. Go to "Manage Employees" tab
2. Click "Add Employee" button
3. Fill in employee details:
   • Name, ID, Department
   • Contact information
   • Work location
4. Save employee record
5. QR code will be generated automatically

📊 STEP 3: TRACK ATTENDANCE
1. Use QR Scanner to scan employee QR codes
2. Or use Manual Entry for quick check-in/out
3. View daily attendance in Dashboard
4. Check attendance history in Reports

📄 STEP 4: GENERATE REPORTS
1. Go to "Reports" tab
2. Select report type and date range
3. Click "Generate Report"
4. Export to Excel if needed

⚙️ STEP 5: SYSTEM CONFIGURATION
1. Go to "Settings" tab
2. Configure:
   • Work start time
   • Late allowance period
   • Theme and language
   • Sync settings

🔄 STEP 6: SYNC & BACKUP
1. System automatically syncs with cloud
2. Manual sync available in Sync menu
3. Check sync status regularly
4. Backup data is maintained automatically

💡 TIPS FOR SUCCESS:
• Keep employee QR codes accessible
• Regular data backup and sync
• Monitor attendance reports daily
• Update employee information as needed
• Use keyboard shortcuts for efficiency

❓ NEED HELP?
• Press F1 for full user manual
• Check Help menu for more options
• Contact support if needed

🎯 YOU'RE READY TO GO!
Your attendance system is now configured and ready to use.
        """
        
        self._show_help_dialog("🚀 Quick Start Guide", guide_text)

    def _show_keyboard_shortcuts(self):
        """Show keyboard shortcuts reference"""
        shortcuts_text = """
⌨️ KEYBOARD SHORTCUTS REFERENCE

🎯 GENERAL SHORTCUTS:
• F1 - User Manual
• F2 - Scan QR Code
• F3 - Manual Entry
• F5 - Record Attendance
• F6 - View Attendance
• F7 - Attendance History
• F12 - Sync Now
• Ctrl+Q - Exit Application
• Ctrl+S - Save Settings

👥 EMPLOYEE MANAGEMENT:
• Ctrl+E - Add Employee
• Ctrl+Shift+E - Edit Employee
• Ctrl+Del - Delete Employee
• Ctrl+F - Search Employee
• Ctrl+L - Employee List
• Ctrl+U - Add User
• Ctrl+Shift+U - Edit User

📄 REPORTS & DATA:
• Ctrl+R - Generate Reports
• Ctrl+Shift+R - Attendance Reports
• Ctrl+D - Daily Summary
• Ctrl+P - Print Reports
• Ctrl+O - Open Project
• Ctrl+N - New Project

🔄 SYNC & UPDATES:
• F12 - Force Sync Now
• Ctrl+Shift+A - AI Assistant
• Ctrl+Shift+L - Advanced Analytics
• Ctrl+, - General Settings

🔍 NAVIGATION:
• Tab - Next field
• Shift+Tab - Previous field
• Enter - Confirm/Submit
• Escape - Cancel/Close
• Ctrl+Tab - Next tab
• Ctrl+Shift+Tab - Previous tab

📊 DASHBOARD:
• Ctrl+1 - Dashboard tab
• Ctrl+2 - Employees tab
• Ctrl+3 - Reports tab
• Ctrl+4 - Search tab
• Ctrl+5 - Settings tab

⚙️ SYSTEM:
• Alt+F4 - Close application
• Ctrl+Alt+Del - Task manager
• Windows+D - Show desktop
• Windows+L - Lock computer

💡 TIPS:
• Most shortcuts work globally in the application
• Some shortcuts are context-sensitive
• You can customize shortcuts in Settings
• Hover over buttons to see tooltips with shortcuts

🎯 EFFICIENCY TIPS:
• Use F1-F12 keys for quick access
• Combine Ctrl+key for advanced functions
• Use Tab navigation for form filling
• Master the most common shortcuts for your workflow
        """
        
        self._show_help_dialog("⌨️ Keyboard Shortcuts", shortcuts_text)

    def _show_system_information(self):
        """Show system information"""
        import platform
        import sys
        import os
        from datetime import datetime
        
        # Get system information
        system_info = {
            "OS": platform.system(),
            "OS Version": platform.version(),
            "Architecture": platform.architecture()[0],
            "Python Version": sys.version.split()[0],
            "PyQt Version": "PyQt6",
            "Current User": os.getenv('USERNAME', 'Unknown'),
            "Computer Name": platform.node(),
            "Processor": platform.processor(),
            "Memory": "Available on request"
        }
        
        # Get application information
        current_version = get_current_version()
        app_info = {
            "Application": "Employee Attendance System",
            "Version": current_version,
            "Developer": "Eng. Mohamed Hagag",
            "Organization": "Rabat Foundation",
            "Build Date": "2024",
            "Database": "SQLite + Supabase Hybrid",
            "Sync Status": "Active" if hasattr(self.db_manager, 'has_supabase_changes') else "Local Only"
        }
        
        # Format system information
        system_text = f"""
💻 SYSTEM INFORMATION

🖥️ COMPUTER DETAILS:
• Operating System: {system_info['OS']} {system_info['OS Version']}
• Architecture: {system_info['Architecture']}
• Processor: {system_info['Processor']}
• Computer Name: {system_info['Computer Name']}
• Current User: {system_info['Current User']}

🐍 SOFTWARE ENVIRONMENT:
• Python Version: {system_info['Python Version']}
• GUI Framework: {system_info['PyQt Version']}
• Application Version: {app_info['Version']}

📱 APPLICATION DETAILS:
• Application Name: {app_info['Application']}
• Developer: {app_info['Developer']}
• Organization: {app_info['Organization']}
• Build Date: {app_info['Build Date']}
• Database System: {app_info['Database']}
• Sync Status: {app_info['Sync Status']}

🔄 SYSTEM STATUS:
• Last Sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Database Status: {'Connected' if self.db_manager else 'Disconnected'}
• Notifications: {'Enabled' if getattr(self, 'notifications_enabled', True) else 'Disabled'}
• Auto Updates: {'Enabled' if hasattr(self, 'auto_refresh_timer') else 'Disabled'}

📊 PERFORMANCE:
• Memory Usage: Available on request
• CPU Usage: Available on request
• Disk Space: Available on request
• Network Status: {'Connected' if hasattr(self.db_manager, 'has_supabase_changes') else 'Local Only'}

🔧 TECHNICAL DETAILS:
• Configuration File: config/settings.json
• Database File: attendance.db
• Log File: logs/app.log
• Backup Location: backups/
• Sync Interval: 30 seconds
• Auto Refresh: 15 seconds

📞 SUPPORT INFORMATION:
• Support Email: support@rabatfoundation.org
• Documentation: Available in Help menu
• Update Server: Configured
• Backup System: Active

🔄 LAST UPDATED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        self._show_help_dialog("💻 System Information", system_text)

    def _show_support_contact(self):
        """Show support and contact information"""
        support_text = """
📞 SUPPORT & CONTACT INFORMATION

🏢 RABAT FOUNDATION IT DEPARTMENT

📧 EMAIL SUPPORT:
• General Support: support@rabatfoundation.org
• Technical Issues: tech@rabatfoundation.org
• System Administrator: admin@rabatfoundation.org
• Emergency Support: emergency@rabatfoundation.org

📱 PHONE SUPPORT:
• Main Office: +20-XXX-XXXX-XXX
• IT Department: +20-XXX-XXXX-XXX
• Emergency Line: +20-XXX-XXXX-XXX
• Support Hours: 9:00 AM - 5:00 PM (Sunday-Thursday)

🏢 OFFICE LOCATION:
• Address: Rabat Foundation Headquarters
• City: [Your City]
• Country: Egypt
• Office Hours: 8:00 AM - 4:00 PM

👨‍💻 TECHNICAL TEAM:
• System Developer: Eng. Mohamed Hagag
• Planning Engineer: Eng. Mohamed Hagag
• IT Manager: [IT Manager Name]
• Database Administrator: [DBA Name]

🆘 SUPPORT LEVELS:

🟢 LEVEL 1 - BASIC SUPPORT:
• Password resets
• Basic usage questions
• Account issues
• Response Time: 2-4 hours

🟡 LEVEL 2 - TECHNICAL SUPPORT:
• System configuration
• Data synchronization issues
• Report generation problems
• Response Time: 4-8 hours

🔴 LEVEL 3 - ADVANCED SUPPORT:
• System errors and bugs
• Database issues
• Performance problems
• Response Time: 8-24 hours

📋 BEFORE CONTACTING SUPPORT:

1. Check the User Manual (F1)
2. Try the Quick Start Guide
3. Check System Information for errors
4. Restart the application
5. Check your internet connection
6. Note down the exact error message

📝 WHEN REPORTING ISSUES:

Please include:
• Your name and employee ID
• Detailed description of the problem
• Steps to reproduce the issue
• Screenshots if applicable
• Error messages (if any)
• System information (Help > System Information)

🔄 MAINTENANCE SCHEDULE:
• Daily: 2:00 AM - 3:00 AM
• Weekly: Friday 11:00 PM - Saturday 1:00 AM
• Monthly: First Sunday of each month

📚 ADDITIONAL RESOURCES:
• User Manual: Help > User Manual
• Quick Start Guide: Help > Quick Start Guide
• System Information: Help > System Information
• Keyboard Shortcuts: Help > Keyboard Shortcuts

🌐 ONLINE RESOURCES:
• Company Website: www.rabatfoundation.org
• IT Portal: [IT Portal URL]
• Knowledge Base: [Knowledge Base URL]
• Training Materials: [Training URL]

⏰ SUPPORT AVAILABILITY:
• Monday - Thursday: 9:00 AM - 5:00 PM
• Friday: 9:00 AM - 12:00 PM
• Saturday - Sunday: Emergency only
• Holidays: Emergency only

📞 EMERGENCY CONTACT:
For critical system issues outside business hours:
• Emergency Line: +20-XXX-XXXX-XXX
• Emergency Email: emergency@rabatfoundation.org
• Response Time: 1-2 hours
        """
        
        self._show_help_dialog("📞 Support & Contact", support_text)

    def _show_help_dialog(self, title, content):
        """Show help dialog with formatted content"""
        dialog = QMessageBox(self)
        dialog.setWindowTitle(title)
        dialog.setText(content)
        dialog.setDetailedText("For more information, contact the IT department.")
        
        # Set dialog properties
        dialog.setStandardButtons(QMessageBox.StandardButton.Ok)
        dialog.setDefaultButton(QMessageBox.StandardButton.Ok)
        
        # Set icon based on title
        if "Manual" in title:
            dialog.setIcon(QMessageBox.Icon.Information)
        elif "Guide" in title:
            dialog.setIcon(QMessageBox.Icon.Information)
        elif "Shortcuts" in title:
            dialog.setIcon(QMessageBox.Icon.Information)
        elif "System" in title:
            dialog.setIcon(QMessageBox.Icon.Information)
        elif "Support" in title:
            dialog.setIcon(QMessageBox.Icon.Information)
        else:
            dialog.setIcon(QMessageBox.Icon.Information)
        
        # Set dialog size
        dialog.setMinimumSize(600, 400)
        
        # Show dialog
        dialog.exec()

    def _show_about(self):
        """Enhanced About dialog"""
        current_version = get_current_version()
        message = f"""
🏢 EMPLOYEE ATTENDANCE SYSTEM
Version: {current_version}

👨‍💻 DEVELOPED BY:
Eng. Mohamed Hagag
Planning Engineer
Rabat Foundation

🏢 ORGANIZATION:
Rabat Foundation
Professional HR Management Solutions

📅 BUILD INFORMATION:
• Build Date: 2024
• Framework: Python + PyQt6
• Database: SQLite + Supabase Hybrid
• Architecture: Modern Desktop Application

🎯 SYSTEM OVERVIEW:
A comprehensive attendance management system designed to streamline HR operations and improve daily tracking efficiency.

✨ KEY FEATURES:
• Real-time attendance tracking
• QR code-based check-in/out
• Advanced reporting system
• Multi-location support
• Cloud synchronization
• Multi-language support
• Automated updates

🔧 TECHNICAL SPECIFICATIONS:
• Built with Python 3.8+
• PyQt6 for modern GUI
• SQLite for local storage
• Supabase for cloud sync
• Excel export functionality
• GPS location tracking

📊 SYSTEM CAPABILITIES:
• Employee management
• Attendance tracking
• Report generation
• Data synchronization
• User management
• Holiday management
• Location management

🔄 UPDATE SYSTEM:
• Automatic update checks
• Manual update option
• Version control
• Backup and restore

📞 SUPPORT:
For technical support or questions:
• Email: support@rabatfoundation.org
• Phone: +20-XXX-XXXX-XXX
• Office: Rabat Foundation IT Department

🌐 ONLINE RESOURCES:
• User Manual: Press F1
• Quick Start Guide: Help menu
• System Information: Help menu
• Keyboard Shortcuts: Help menu

© 2024 Rabat Foundation. All rights reserved.
This software is proprietary and confidential.
        """
        
        box = QMessageBox(self)
        box.setWindowTitle("ℹ️ About - Employee Attendance System")
        box.setText(message)
        box.setIcon(QMessageBox.Icon.Information)
        
        # Set dialog size
        box.setMinimumSize(500, 400)
        
        try:
            from app.utils.resources import resource_path
            import os
            logo_path = resource_path('assets/icons/rabat-logo.jpg')
            if os.path.exists(logo_path):
                pix = QPixmap(logo_path)
                if not pix.isNull():
                    box.setIconPixmap(pix.scaledToWidth(96, Qt.TransformationMode.SmoothTransformation))
            else:
                # fallback to app icon if exists
                app_icon_path = resource_path('assets/icons/app.png')
                if os.path.exists(app_icon_path):
                    pix = QPixmap(app_icon_path)
                    if not pix.isNull():
                        box.setIconPixmap(pix.scaledToWidth(96, Qt.TransformationMode.SmoothTransformation))
        except Exception:
            pass
        
        box.exec()

    def closeEvent(self, event):
        # ضمان إيقاف الخيوط الخلفية قبل الغلق
        self.stop_notifier_service()
        
        # تنظيف مدير التنبيهات المتقدم
        try:
            if hasattr(self, 'notifications_manager') and self.notifications_manager:
                self.notifications_manager.cleanup()
                self.logger.info("🔄 Advanced Notifications Manager cleanup completed")
        except Exception as e:
            self.logger.error(f"Error during notifications manager cleanup: {e}")
        
        # تنظيف قاعدة البيانات الهجين عند الخروج
        try:
            if hasattr(self.db_manager, 'cleanup_on_exit'):
                self.db_manager.cleanup_on_exit()
                self.logger.info("🔄 Hybrid database cleanup completed (local operations + cleanup)")
        except Exception as e:
            self.logger.error(f"Error during database cleanup: {e}")
        
        super().closeEvent(event)

    def start_auto_refresh_timer(self):
        """
        مؤقت Update دوري خفيف لUpdate لوحة التحكم تلقائيًا.
        الافتراضي 15 ثانية ويمكن Edit الفترة لاحقًا من الإعدادات.
        """
        try:
            interval_seconds = int(self.app_settings.get('dashboard_refresh_seconds', '15'))
        except Exception:
            interval_seconds = 15
        self.auto_refresh_timer = QTimer(self)
        self.auto_refresh_timer.timeout.connect(self.update_dashboard_table)
        self.auto_refresh_timer.start(max(5, interval_seconds) * 1000)
        self.logger.info(f"Auto-refresh timer started: every {max(5, interval_seconds)}s")

    # 🆕 --- نظام كشف التغييرات الذكي ---
    def start_change_detection_system(self):
        """Start change detection system in Supabase"""
        try:
            # Change check timer (every minute)
            self.change_check_timer = QTimer(self)
            self.change_check_timer.timeout.connect(self.check_supabase_changes)
            self.change_check_timer.start(60000)  # 60 seconds
            
            # Check changes immediately when system starts
            QTimer.singleShot(2000, self.check_supabase_changes)  # Check after 2 seconds
            
            self.logger.info("✅ Smart change detection system started")
            
        except Exception as e:
            self.logger.error(f"❌ Error starting change detection system: {e}")
    
    def check_supabase_changes(self):
        """Check for changes in Supabase"""
        try:
            if hasattr(self.db_manager, 'has_supabase_changes'):
                if self.db_manager.has_supabase_changes():
                    # Get change information
                    change_info = self.db_manager.get_change_info()
                    change_count = change_info.get('change_count', 0)
                    
                    # Update change indicators with counter
                    self._update_change_indicators(change_count)
                    
                    # Show notification immediately
                    self.show_change_notification()
                    
                    self.logger.info(f"🔄 Discovered {change_count} changes in Supabase")
        except Exception as e:
            self.logger.error(f"❌ Error checking for changes: {e}")
    
    def _update_change_indicators(self, change_count):
        """Update change indicators with counter"""
        try:
            if change_count > 0:
                # Show change indicator
                self.change_indicator_action.setVisible(True)
                
                # Show change counter with red dot
                self.change_counter_action.setText(f"🔴 {change_count}")
                self.change_counter_action.setVisible(True)
                
                # Update tooltip
                self.change_counter_action.setToolTip(f"Number of new changes: {change_count}")
                
                self.logger.info(f"🔴 Updated change indicators: {change_count} changes")
            else:
                # Hide indicators when no changes exist
                self.change_indicator_action.setVisible(False)
                self.change_counter_action.setVisible(False)
                
        except Exception as e:
            self.logger.error(f"❌ Error updating change indicators: {e}")
    
    def show_change_notification(self):
        """Show change notifications in a gentle way"""
        try:
            # Check notification settings
            if not getattr(self, 'notifications_enabled', True):
                return
            
            change_info = self.db_manager.get_change_info()
            change_count = change_info.get('change_count', 0)
            
            # Create gentle notification from bottom
            self.show_gentle_notification(
                "🔄 New Updates Available",
                f"Discovered {change_count} updates in shared database",
                "info"
            )
            
            # Update counter in interface
            if change_count > 0:
                self._update_change_indicators(change_count)
            
        except Exception as e:
            self.logger.error(f"❌ Error showing change notification: {e}")
    
    def show_gentle_notification(self, title: str, message: str, notification_type: str = "info"):
        """إظهار إشعار لطيف من الأسفل"""
        try:
            # إنشاء نافذة إشعار لطيفة
            notification = GentleNotification(self, title, message, notification_type)
            
            # عرض الإشعار من الأسفل
            self.show_notification_at_bottom(notification)
            
        except Exception as e:
            self.logger.error(f"❌ Error في إظهار الإشعار اللطيف: {e}")
    
    def show_notification_at_bottom(self, notification):
        """عرض الإشعار من أسفل النافذة"""
        try:
            # حساب موقع الإشعار (أسفل النافذة)
            window_rect = self.geometry()
            x, y, width, height = window_rect.x(), window_rect.y(), window_rect.width(), window_rect.height()
            
            # موقع الإشعار (أسفل النافذة، في المنتصف)
            notification_x = x + (width - notification.width()) // 2
            notification_y = y + height - notification.height() - 50  # 50 بكسل من الأسفل
            
            notification.move(notification_x, notification_y)
            notification.show()
            
            # إخفاء الإشعار تلقائياً بعد 5 ثوانٍ
            QTimer.singleShot(5000, notification.hide)
            
        except Exception as e:
            self.logger.error(f"❌ Error في عرض الإشعار: {e}")
    

    
    def smart_refresh_data(self):
        """Smart data update from Supabase"""
        try:
            self.logger.info("🔄 Starting smart data update...")
            
            # Show loading indicator
            self.smart_refresh_action.setText("⏳ Updating...")
            self.smart_refresh_action.setEnabled(False)
            
            # Update data
            if hasattr(self.db_manager, 'force_full_sync'):
                success = self.db_manager.force_full_sync()
                if success:
                    # Update all interfaces
                    self.update_all_widgets()
                    
                    # Hide change indicators
                    self.change_indicator_action.setVisible(False)
                    self.change_counter_action.setVisible(False)
                    
                    # Success notification
                    self.show_gentle_notification(
                        "✅ Update Successful",
                        "All data has been successfully updated from shared database!",
                        "success"
                    )
                    
                    # Additional confirmation message
                    QMessageBox.information(
                        self,
                        "🔄 Update Successful",
                        """All data has been updated successfully!

📊 What was updated:
• Dashboard and tables
• Employee list
• Reports and statistics
• Locations and holidays
• Users and settings

Now you can see all new updates in all tabs!"""
                    )
                    
                    self.logger.info("✅ Smart update completed successfully")
                else:
                    # Warning notification
                    self.show_gentle_notification(
                        "⚠️ Warning",
                        "Failed to update data. Please try again.",
                        "warning"
                    )
                    self.logger.warning("⚠️ Smart update failed")
            
            # Re-enable button
            self.smart_refresh_action.setText("🔄 Update Data")
            self.smart_refresh_action.setEnabled(True)
            
        except Exception as e:
            self.logger.error(f"❌ Error in smart update: {e}")
            # Error notification
            self.show_gentle_notification(
                "❌ Error",
                f"An error occurred during update: {str(e)}",
                "error"
            )
            self.smart_refresh_action.setText("🔄 Update Data")
            self.smart_refresh_action.setEnabled(True)
    
    def update_all_widgets(self):
        """Update all interfaces"""
        try:
            self.logger.info("🔄 Starting update of all interfaces...")
            
            # 1. Update dashboard
            if hasattr(self, 'update_dashboard_table'):
                self.update_dashboard_table()
                self.logger.info("✅ Dashboard updated")
            
            # 2. Update dashboard tables
            if hasattr(self, 'checkin_table') and hasattr(self, 'checkout_table'):
                self._refresh_dashboard_tables()
                self.logger.info("✅ Dashboard tables updated")
            
            # 2. Update different tabs
            if hasattr(self, 'tabs') and self.tabs.count() > 0:
                for i in range(self.tabs.count()):
                    widget = self.tabs.widget(i)
                    self._refresh_widget_data(widget)
            
            # 3. Update locations cache
            if hasattr(self, 'locations_cache'):
                self.locations_cache = {loc['id']: loc for loc in (self.db_manager.get_all_locations() or [])}
                self.logger.info("✅ Locations cache updated")
            
            # 4. Update change indicators
            if hasattr(self, 'change_indicator_action'):
                self.change_indicator_action.setVisible(False)
            if hasattr(self, 'change_counter_action'):
                self.change_counter_action.setVisible(False)
            
            self.logger.info("✅ All interfaces updated successfully")
            
        except Exception as e:
            self.logger.error(f"❌ Error updating interfaces: {e}")
    
    def _refresh_widget_data(self, widget):
        """Update data for specific widget"""
        try:
            widget_name = widget.__class__.__name__
            
            # Update based on widget type
            if hasattr(widget, 'refresh_data'):
                # If widget has refresh_data function
                widget.refresh_data()
                self.logger.info(f"✅ Updated {widget_name} using refresh_data")
                
            elif hasattr(widget, 'load_data'):
                # If widget has load_data function
                widget.load_data()
                self.logger.info(f"✅ Updated {widget_name} using load_data")
                
            elif hasattr(widget, 'update_table'):
                # If widget has update_table function
                widget.update_table()
                self.logger.info(f"✅ Updated {widget_name} using update_table")
                
            elif hasattr(widget, 'reload_data'):
                # If widget has reload_data function
                widget.reload_data()
                self.logger.info(f"✅ Updated {widget_name} using reload_data")
                
            elif hasattr(widget, 'refresh'):
                # If widget has refresh function
                widget.refresh()
                self.logger.info(f"✅ Updated {widget_name} using refresh")
                
            else:
                # Manual update attempt for known widgets
                self._manual_widget_refresh(widget, widget_name)
                
        except Exception as e:
            self.logger.error(f"❌ Error updating {widget.__class__.__name__}: {e}")
    
    def _manual_widget_refresh(self, widget, widget_name):
        """Manual update for known widgets"""
        try:
            if 'EmployeesWidget' in widget_name:
                # Update employee list
                if hasattr(widget, 'load_employees_data'):
                    widget.load_employees_data()
                elif hasattr(widget, 'load_employees'):
                    widget.load_employees()
                elif hasattr(widget, 'populate_table'):
                    widget.populate_table()
                self.logger.info(f"✅ Manually updated {widget_name}")
                
            elif 'ReportsWidget' in widget_name:
                # Update reports
                if hasattr(widget, 'load_reports'):
                    widget.load_reports()
                elif hasattr(widget, 'generate_reports'):
                    widget.generate_reports()
                self.logger.info(f"✅ Manually updated {widget_name}")
                
            elif 'SearchWidget' in widget_name:
                # Update search
                if hasattr(widget, 'load_employees_data'):
                    widget.load_employees_data()
                elif hasattr(widget, 'clear_search'):
                    widget.clear_search()
                self.logger.info(f"✅ Manually updated {widget_name}")
                
            elif 'LocationsWidget' in widget_name:
                # Update locations
                if hasattr(widget, 'load_locations_data'):
                    widget.load_locations_data()
                elif hasattr(widget, 'load_locations'):
                    widget.load_locations()
                elif hasattr(widget, 'populate_table'):
                    widget.populate_table()
                self.logger.info(f"✅ Manually updated {widget_name}")
                
            elif 'HolidaysWidget' in widget_name:
                # Update holidays
                if hasattr(widget, 'load_holidays_data'):
                    widget.load_holidays_data()
                elif hasattr(widget, 'load_holidays'):
                    widget.load_holidays()
                elif hasattr(widget, 'populate_table'):
                    widget.populate_table()
                self.logger.info(f"✅ Manually updated {widget_name}")
                
            elif 'UsersWidget' in widget_name:
                # Update users
                if hasattr(widget, 'load_users_data'):
                    widget.load_users_data()
                elif hasattr(widget, 'load_users'):
                    widget.load_users()
                elif hasattr(widget, 'populate_table'):
                    widget.populate_table()
                self.logger.info(f"✅ Manually updated {widget_name}")
                
            else:
                self.logger.info(f"ℹ️ No known update method for {widget_name}")
                
        except Exception as e:
            self.logger.error(f"❌ Error in manual update for {widget_name}: {e}")
    
    def manual_check_changes(self):
        """Manually check for changes"""
        try:
            self.logger.info("🔍 Starting manual change check...")
            
            # Check for changes
            if hasattr(self.db_manager, 'has_supabase_changes'):
                if self.db_manager.has_supabase_changes():
                    change_info = self.db_manager.get_change_info()
                    change_count = change_info.get('change_count', 0)
                    
                    # Update indicators
                    self._update_change_indicators(change_count)
                    
                    # Show notification
                    self.show_gentle_notification(
                        "🔍 Changes Checked",
                        f"Discovered {change_count} new updates",
                        "info"
                    )
                    
                    self.logger.info(f"✅ Discovered {change_count} changes")
                else:
                    # Hide indicators
                    self._update_change_indicators(0)
                    
                    # No changes notification
                    self.show_gentle_notification(
                        "🔍 Changes Checked",
                        "No new updates available",
                        "success"
                    )
                    
                    self.logger.info("✅ No new changes available")
            else:
                self.logger.error("❌ Change check function not available")
                
        except Exception as e:
            self.logger.error(f"❌ Error in manual check: {e}")
            self.show_gentle_notification(
                "❌ Error",
                f"Failed to check for changes: {str(e)}",
                "error"
            )
    
    def _refresh_dashboard_tables(self):
        """Update dashboard tables"""
        try:
            # Update check-in table
            if hasattr(self, 'checkin_table'):
                self.checkin_table.clearContents()
                self.checkin_table.setRowCount(0)
            
            # Update check-out table
            if hasattr(self, 'checkout_table'):
                self.checkout_table.clearContents()
                self.checkout_table.setRowCount(0)
            
            # Reload data
            self.update_dashboard_table()
            
        except Exception as e:
            self.logger.error(f"❌ Error updating dashboard tables: {e}")
    
    def show_sync_info(self):
        """Display sync status information"""
        try:
            if hasattr(self.db_manager, 'get_sync_status'):
                sync_status = self.db_manager.get_sync_status()
                change_info = self.db_manager.get_change_info()
                
                message = f"""📊 Sync Information:

🔄 Sync Status:
• Enabled: {'Yes' if sync_status.get('sync_enabled') else 'No'}
• Auto Sync: {'Enabled' if sync_status.get('auto_sync_enabled') else 'Disabled'}
• Last Sync: {sync_status.get('last_sync_time', 'Unknown')}

📈 Change Information:
• Has Changes: {'Yes' if change_info.get('has_changes') else 'No'}
• Change Count: {change_info.get('change_count', 0)}
• Last Check: {change_info.get('last_check', 'Unknown')}

⚙️ System Settings:
• Change Check: Every 60 seconds
• Auto Sync: Every 2-3 seconds
• Hybrid System: Enabled"""
                
                # Information notification
                self.show_gentle_notification(
                    "📊 Sync Information",
                    "Sync information displayed successfully",
                    "info"
                )
            else:
                # Warning notification
                self.show_gentle_notification(
                    "📊 Sync Information",
                    "Sync information not available currently.",
                    "warning"
                )
                
        except Exception as e:
            self.logger.error(f"❌ Error displaying sync information: {e}")
            # Error notification
            self.show_gentle_notification(
                "⚠️ Warning",
                f"Failed to display sync information: {str(e)}",
                "error"
            )
    
    def toggle_notifications(self):
        """Enable/Disable automatic notifications"""
        try:
            self.notifications_enabled = not self.notifications_enabled
            
            if self.notifications_enabled:
                self.toggle_notifications_action.setText("🔕 Disable Notifications")
                self.toggle_notifications_action.setToolTip("Disable automatic notifications")
                # Success notification
                self.show_gentle_notification(
                    "🔔 Notifications Enabled",
                    "Automatic notifications will appear when updates are available",
                    "success"
                )
            else:
                self.toggle_notifications_action.setText("🔔 Enable Notifications")
                self.toggle_notifications_action.setToolTip("Enable automatic notifications")
                # Information notification
                self.show_gentle_notification(
                    "🔕 Notifications Disabled",
                    "Automatic notifications will not appear anymore",
                    "info"
                )
            
            self.logger.info(f"Notifications {'enabled' if self.notifications_enabled else 'disabled'}")
            
        except Exception as e:
            self.logger.error(f"❌ Error toggling notification status: {e}")

    # --- Updateات التطبيق ---
    def _check_for_updates_clicked(self):
        self.perform_update_check(interactive=True)
    
    def _open_qr_scanner(self):
        """Open QR code scanner window"""
        try:
            from app.gui.qr_scanner_dialog import QRScannerDialog
            dialog = QRScannerDialog(db_manager=self.db_manager, parent=self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to open QR Scanner:\n{str(e)}")
    
    def _open_qr_settings(self):
        """Open general QR code settings window"""
        try:
            from app.gui.qr_settings_dialog import QRSettingsDialog
            dialog = QRSettingsDialog(self)
            dialog.settings_changed.connect(self._on_qr_settings_changed)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to open QR Settings:\n{str(e)}")
    
    def _open_advanced_qr_tools(self):
        """Open advanced QR code tools window"""
        try:
            from app.gui.advanced_qr_tools import AdvancedQRToolsDialog
            dialog = AdvancedQRToolsDialog(self)
            dialog.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to open Advanced QR Tools:\n{str(e)}")
    
    def _on_qr_settings_changed(self, new_settings):
        """Handle change in general QR settings"""
        try:
            # Update all existing QR codes
            from app.utils.qr_manager import QRCodeManager
            qr_manager = QRCodeManager()
            qr_manager.update_settings(new_settings)
            
            # Regenerate all QR codes
            self._regenerate_all_qr_codes(new_settings)
            
            QMessageBox.information(self, "Success", 
                                  "New settings applied to all QR codes successfully!")
            
        except Exception as e:
            QMessageBox.warning(self, "Warning", 
                              f"Settings updated but failed to regenerate QR codes:\n{str(e)}")
    
    def _regenerate_all_qr_codes(self, settings):
        """Regenerate all QR codes with new settings"""
        try:
            from app.database.database_manager import DatabaseManager
            db_manager = DatabaseManager()
            from app.utils.qr_manager import QRCodeManager
            qr_manager = QRCodeManager()
            
            # Get all employees
            employees = db_manager.get_all_employees()
            
            success_count = 0
            for employee in employees:
                try:
                    # Create new QR code with new settings
                    qr_code = qr_manager.generate_qr_code(employee)
                    if qr_code:
                        # Save الرمز الجديد
                        db_manager.update_employee_qr_code(employee['id'], qr_code)
                        success_count += 1
                        print(f"✅ QR code updated for employee: {employee.get('name')}")
                except Exception as e:
                    print(f"❌ Failed to update QR code for employee {employee.get('name')}: {e}")
            
            print(f"Updated {success_count} out of {len(employees)} QR codes")
            
        except Exception as e:
            print(f"Error regenerating QR codes: {e}")
            raise

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
            
            # تحميل الملف
            local_path = download_file(url)
            if not local_path:
                QMessageBox.critical(self, self.tr("Updates"), self.tr("Failed to download the update."))
                return
            
            # التحقق من صحة الملف
            from app.utils.update_checker import verify_installer_file
            if not verify_installer_file(local_path):
                QMessageBox.critical(self, self.tr("Updates"), self.tr("Downloaded file is invalid or corrupted."))
                return
            
            # تشغيل المثبت
            ok = run_windows_installer(local_path, silent=True)
            if ok:
                QMessageBox.information(
                    self, 
                    self.tr("Updates"), 
                    self.tr("Installer started successfully. The application may close or restart during update.")
                )
                # Close التطبيق بعد الUpdate
                QTimer.singleShot(3000, self.close)
            else:
                QMessageBox.warning(
                    self, 
                    self.tr("Updates"), 
                    self.tr("Could not start installer automatically. Please run it manually from: ") + local_path
                )
        except Exception as e:
            self.logger.error(f"Update installation failed: {e}")
            QMessageBox.critical(self, self.tr("Updates"), f"{self.tr('Update failed')}: {e}")
        finally:
            self.statusBar().clearMessage()
    
    def apply_tab_styling(self):
        """تطبيق تنسيق جميل ومتقدم للتبويبات"""
        try:
            # تنسيق CSS متقدم للتبويبات
            tab_style = """
            QTabWidget::pane {
                border: 2px solid #C0C0C0;
                border-radius: 8px;
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #F8F9FA, stop:1 #E9ECEF);
                margin-top: 2px;
            }
            
            QTabWidget::tab-bar {
                alignment: left;
            }
            
            QTabBar::tab {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E3F2FD, stop:1 #BBDEFB);
                border: 1px solid #90CAF9;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 120px;
                padding: 8px 16px;
                margin-right: 2px;
                font-weight: 500;
                color: #1565C0;
            }
            
            QTabBar::tab:selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #FFFFFF, stop:1 #F5F5F5);
                border: 2px solid #2196F3;
                border-bottom: 2px solid #FFFFFF;
                color: #0D47A1;
                font-weight: 600;
            }
            
            QTabBar::tab:hover:!selected {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E1F5FE, stop:1 #B3E5FC);
                border: 1px solid #4FC3F7;
                color: #0277BD;
            }
            
            QTabBar::tab:first {
                margin-left: 4px;
            }
            
            QTabBar::tab:last {
                margin-right: 4px;
            }
            
            QTabBar::tab:only-one {
                margin: 0 4px;
            }
            
            QTabBar::scroller {
                width: 20px;
            }
            
            QTabBar QToolButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #F5F5F5, stop:1 #E0E0E0);
                border: 1px solid #BDBDBD;
                border-radius: 4px;
                margin: 2px;
            }
            
            QTabBar QToolButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #E3F2FD, stop:1 #BBDEFB);
                border: 1px solid #2196F3;
            }
            
            QTabBar QToolButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #BBDEFB, stop:1 #90CAF9);
            }
            """
            
            # تطبيق التنسيق
            self.tabs.setStyleSheet(tab_style)
            
            # إضافة تأثيرات إضافية
            self.tabs.setDocumentMode(False)
            self.tabs.setElideMode(Qt.TextElideMode.ElideRight)
            
            print("✅ تم تطبيق تنسيق التبويبات المتقدم بنجاح")
            
        except Exception as e:
            print(f"❌ خطأ في تطبيق تنسيق التبويبات: {e}")
            import traceback
            traceback.print_exc()