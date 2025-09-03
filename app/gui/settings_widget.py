from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QPushButton, QMessageBox, 
    QGroupBox, QTimeEdit, QSpinBox, QLabel, QHBoxLayout, QProgressBar
)
from PyQt6.QtCore import QTime, QCoreApplication, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from app.database.database_manager import DatabaseManager
import logging

logger = logging.getLogger(__name__)

class SettingsWidget(QWidget):
    """
    Comprehensive settings interface for manager.
    تدير المظهر، قواعد العمل، ومستخدمي البرنامج.
    """
    # تعريف الإشارات التي سيتم إصدارها عند تغيير الإعدادات
    theme_changed = pyqtSignal(str) # إشارة تحمل اسم الثيم الجديد
    language_changed = pyqtSignal(str) # إشارة تحمل كود اللغة الجديد

    def __init__(self):
        super().__init__()
        # محاولة استخدام SimpleHybridManager إذا كان متاحاً
        try:
            from app.database.simple_hybrid_manager import SimpleHybridManager
            self.db_manager = SimpleHybridManager()
        except ImportError:
            from app.database.database_manager import DatabaseManager
            self.db_manager = DatabaseManager()
        
        self.current_settings = {} # لتخزين الإعدادات الحالية للمقارنة
        
        self.setup_ui()
        self.connect_signals()
        self.load_settings()

    def setup_ui(self):
        """تنشئ وتنظم كل عناصر الواجهة."""
        layout = QVBoxLayout(self)
        
        # --- مجموعة المظهر واللغة ---
        appearance_group = QGroupBox(self.tr("Appearance & Language"))
        appearance_layout = QFormLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        appearance_layout.addRow(f"{self.tr('Application Theme')}:", self.theme_combo)
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["en", "ar"])
        appearance_layout.addRow(f"{self.tr('Interface Language')}:", self.lang_combo)
        appearance_group.setLayout(appearance_layout)
        layout.addWidget(appearance_group)

        # --- مجموعة قواعد العمل ---
        work_group = QGroupBox(self.tr("Work Rules"))
        work_layout = QFormLayout()
        self.start_time_edit = QTimeEdit()
        self.start_time_edit.setDisplayFormat("hh:mm:ss ap")
        work_layout.addRow(f"{self.tr('Official Work Start Time')}:", self.start_time_edit)
        self.late_allowance_spin = QSpinBox()
        self.late_allowance_spin.setRange(0, 120)
        self.late_allowance_spin.setSuffix(f" {self.tr('minutes')}")
        work_layout.addRow(f"{self.tr('Late Allowance Period')}:", self.late_allowance_spin)
        work_group.setLayout(work_layout)
        layout.addWidget(work_group)

        # --- مجموعة قاعدة البيانات الهجين ---
        if hasattr(self.db_manager, 'get_sync_status'):
            sync_group = QGroupBox(self.tr("🔄 Database Sync Status (ONE-TIME Mode)"))
            sync_layout = QFormLayout()
            
            # حالة النظام
            self.system_status_label = QLabel("🚀 One-Time Sync System Active")
            self.system_status_label.setStyleSheet("color: green; font-weight: bold;")
            sync_layout.addRow(f"{self.tr('System Mode')}:", self.system_status_label)
            
            self.sync_status_label = QLabel("Checking...")
            self.sync_status_label.setStyleSheet("color: blue;")
            sync_layout.addRow(f"{self.tr('Sync Status')}:", self.sync_status_label)
            
            self.pending_changes_label = QLabel("0")
            sync_layout.addRow(f"{self.tr('Pending Changes')}:", self.pending_changes_label)
            
            self.last_sync_label = QLabel("Never")
            sync_layout.addRow(f"{self.tr('Last Sync')}:", self.last_sync_label)
            
            # حالة المزامنة مع الويب
            if hasattr(self.db_manager, 'get_web_sync_status'):
                self.web_sync_label = QLabel("Checking...")
                self.web_sync_label.setStyleSheet("color: blue;")
                sync_layout.addRow(f"{self.tr('Web App Status')}:", self.web_sync_label)
                
                self.vercel_status_label = QLabel("🌐 Vercel")
                self.vercel_status_label.setStyleSheet("color: green; font-weight: bold;")
                sync_layout.addRow(f"{self.tr('Platform')}:", self.vercel_status_label)
            
            # أزرار المزامنة
            sync_buttons_layout = QHBoxLayout()
            self.sync_now_button = QPushButton(f"🔄 {self.tr('Local Sync Only')}")
            self.sync_now_button.clicked.connect(self.sync_now)
            sync_buttons_layout.addWidget(self.sync_now_button)
            
            if hasattr(self.db_manager, 'force_sync_with_web'):
                self.web_sync_button = QPushButton(f"🌐 {self.tr('Web Sync (Disabled)')}")
                self.web_sync_button.clicked.connect(self.sync_with_web)
                self.web_sync_button.setEnabled(False)
                sync_buttons_layout.addWidget(self.web_sync_button)
            
            self.sync_progress = QProgressBar()
            self.sync_progress.setVisible(False)
            sync_buttons_layout.addWidget(self.sync_progress)
            
            sync_layout.addRow("", sync_buttons_layout)
            
            # Information النظام
            info_label = QLabel("📍 All operations are now LOCAL for maximum speed\n🔄 ONE-TIME Supabase sync for initial data download\n🚫 Supabase will be DISABLED after initial sync\n⚡ No more 'not responding' or slow performance!")
            info_label.setStyleSheet("color: blue; font-size: 10px;")
            sync_layout.addRow("", info_label)
            
            sync_group.setLayout(sync_layout)
            layout.addWidget(sync_group)
            
            # مؤقت لUpdate حالة المزامنة
            self.sync_timer = QTimer()
            self.sync_timer.timeout.connect(self.update_sync_status)
            self.sync_timer.start(5000)  # Update كل 5 ثواني

        # --- زر الSave ---
        self.save_button = QPushButton(f"💾 {self.tr('Save Settings')}")
        self.save_button.setFont(QFont("Arial", 12))
        layout.addWidget(self.save_button)
        layout.addStretch()
        
    def connect_signals(self):
        """تربط إشارة زر الSave بالدالة الخاصة بها."""
        self.save_button.clicked.connect(self.save_settings)

    def load_settings(self):
        """تحمل الإعدادات الحالية من قاعدة البيانات وتعرضها في الواجهة."""
        self.current_settings = self.db_manager.get_all_settings()
        self.theme_combo.setCurrentText(self.current_settings.get('theme', 'light'))
        self.lang_combo.setCurrentText(self.current_settings.get('language', 'en'))
        start_time_str = self.current_settings.get('work_start_time', '08:30:00')
        start_time = QTime.fromString(start_time_str, "HH:mm:ss")
        self.start_time_edit.setTime(start_time)
        self.late_allowance_spin.setValue(int(self.current_settings.get('late_allowance_minutes', 15)))

    def save_settings(self):
        """
        تSave الإعدادات الجديدة وتصدر إشارات إذا تغير الثيم أو اللغة.
        """
        new_theme = self.theme_combo.currentText()
        new_lang = self.lang_combo.currentText()
        
        # Save الإعدادات الأخرى دائمًا
        self.db_manager.save_setting('work_start_time', self.start_time_edit.time().toString("HH:mm:ss"))
        self.db_manager.save_setting('late_allowance_minutes', str(self.late_allowance_spin.value()))

        lang_changed = new_lang != self.current_settings.get('language')

        # التحقق من تغيير الثيم وإصدار الإشارة
        if new_theme != self.current_settings.get('theme'):
            # Save الإعداد في قاعدة البيانات
            self.db_manager.save_setting('theme', new_theme)
            
            # Update الإعدادات المحلية
            self.current_settings['theme'] = new_theme
            
            # إصدار الإشارة لتطبيق الثيم
            self.theme_changed.emit(new_theme)
            
            # رسالة Confirm
            QMessageBox.information(self, self.tr("Success"), 
                self.tr(f"Theme changed to {new_theme}. The change will be applied immediately."))

        # التحقق من تغيير اللغة وإصدار الإشارة
        if lang_changed:
            self.db_manager.save_setting('language', new_lang)
            self.language_changed.emit(new_lang)
            # عرض رسالة خاصة للغة لأنها تتطلب إعادة بناء الواجهة
            QMessageBox.information(self, self.tr("Success"), self.tr("Settings saved. Language changes will be applied now."))
        else:
            QMessageBox.information(self, self.tr("Success"), self.tr("Settings saved successfully."))
        
    def update_sync_status(self):
        """Update حالة المزامنة"""
        try:
            status = self.db_manager.get_sync_status()
            
            # Update حالة النظام
            if hasattr(self, 'system_status_label'):
                if status.get('supabase_disabled', False):
                    self.system_status_label.setText("🚫 Supabase DISABLED - Local Only")
                    self.system_status_label.setStyleSheet("color: orange; font-weight: bold;")
                elif status.get('initial_sync_completed', False):
                    self.system_status_label.setText("✅ One-Time Sync Completed")
                    self.system_status_label.setStyleSheet("color: green; font-weight: bold;")
                elif status['hybrid_mode']:
                    self.system_status_label.setText("🔄 One-Time Sync System Active")
                    self.system_status_label.setStyleSheet("color: blue; font-weight: bold;")
                else:
                    self.system_status_label.setText("💾 Local Database Only")
                    self.system_status_label.setStyleSheet("color: orange; font-weight: bold;")
            
            # Update حالة المزامنة
            if status['sync_in_progress']:
                self.sync_status_label.setText("🔄 Syncing...")
                self.sync_status_label.setStyleSheet("color: orange;")
                self.sync_now_button.setEnabled(False)
                if hasattr(self, 'web_sync_button'):
                    self.web_sync_button.setEnabled(False)
            else:
                if status.get('supabase_disabled', False):
                    self.sync_status_label.setText("🚫 Supabase Disabled - Local Only")
                    self.sync_status_label.setStyleSheet("color: orange;")
                elif status['last_error']:
                    self.sync_status_label.setText("❌ Sync Error")
                    self.sync_status_label.setStyleSheet("color: red;")
                else:
                    self.sync_status_label.setText("✅ Local Operations Active")
                    self.sync_status_label.setStyleSheet("color: green;")
                self.sync_now_button.setEnabled(True)
                if hasattr(self, 'web_sync_button'):
                    self.web_sync_button.setEnabled(False)  # دائماً Disabled
            
            # Update التغييرات المعلقة
            self.pending_changes_label.setText(str(status['pending_changes']))
            
            # Update آخر مزامنة
            if status['last_sync']:
                if isinstance(status['last_sync'], str):
                    time_str = status['last_sync']
                else:
                    time_str = status['last_sync'].strftime("%Y-%m-%d %H:%M:%S")
                self.last_sync_label.setText(time_str)
            else:
                self.last_sync_label.setText("Never")
            
            # Update حالة المزامنة مع الويب
            if hasattr(self.db_manager, 'get_web_sync_status'):
                try:
                    web_status = self.db_manager.get_web_sync_status()
                    if web_status.get('supabase_status') == 'disabled_after_initial_sync':
                        self.web_sync_label.setText("🚫 Disabled After Initial Sync")
                        self.web_sync_label.setStyleSheet("color: orange;")
                    elif web_status['web_connected']:
                        self.web_sync_label.setText("✅ Connected")
                        self.web_sync_label.setStyleSheet("color: green;")
                    else:
                        self.web_sync_label.setText("❌ Disconnected")
                        self.web_sync_label.setStyleSheet("color: red;")
                except Exception as e:
                    self.web_sync_label.setText("❌ Error")
                    self.web_sync_label.setStyleSheet("color: red;")
                    
        except Exception as e:
            self.sync_status_label.setText("❌ Error")
            self.sync_status_label.setStyleSheet("color: red;")
            logger.error(f"Error updating sync status: {e}")

    def sync_now(self):
        """مزامنة فورية - محلياً فقط"""
        if hasattr(self.db_manager, 'sync_now'):
            try:
                self.sync_now_button.setEnabled(False)
                self.sync_progress.setVisible(True)
                self.sync_progress.setRange(0, 0)  # Progress bar indeterminate
                
                # بدء المزامنة في خيط منفصل
                import threading
                def sync_worker():
                    try:
                        success = self.db_manager.sync_now()
                        # Update الواجهة في الخيط الرئيسي
                        QTimer.singleShot(0, lambda: self.sync_completed(success))
                    except Exception as e:
                        QTimer.singleShot(0, lambda: self.sync_completed(False, str(e)))
                
                sync_thread = threading.Thread(target=sync_worker, daemon=True)
                sync_thread.start()
                
            except Exception as e:
                QMessageBox.critical(self, self.tr("Error"), f"Failed to start local sync: {str(e)}")
                self.sync_now_button.setEnabled(True)
                self.sync_progress.setVisible(False)
        else:
            QMessageBox.warning(self, self.tr("Not Supported"), self.tr("Local sync not supported by this database manager."))

    def sync_completed(self, success: bool, error_msg: str = None):
        """معالجة اكتمال المزامنة"""
        self.sync_now_button.setEnabled(True)
        if hasattr(self, 'web_sync_button'):
            self.web_sync_button.setEnabled(False)  # دائماً Disabled
        self.sync_progress.setVisible(False)
        
        if success:
            QMessageBox.information(self, self.tr("Success"), self.tr("Local operations completed successfully!"))
        else:
            error_text = error_msg if error_msg else self.tr("Local operations failed")
            QMessageBox.warning(self, self.tr("Local Operations Error"), f"Local operations failed: {error_text}")

    def sync_with_web(self):
        """مزامنة مع تطبيق الويب - Disabled"""
        QMessageBox.information(self, self.tr("Info"), self.tr("Web sync is disabled after initial data download. All operations are now local for maximum performance."))

    def web_sync_completed(self, success: bool, error_msg: str = None):
        """معالجة اكتمال المزامنة مع الويب - Disabled"""
        self.web_sync_button.setEnabled(False)
        self.sync_progress.setVisible(False)
        
        QMessageBox.information(self, self.tr("Info"), self.tr("Web sync is disabled after initial data download. All operations are now local for maximum performance."))

    def tr(self, text):
        """دالة مساعدة للترجمة."""
        return QCoreApplication.translate("SettingsWidget", text)