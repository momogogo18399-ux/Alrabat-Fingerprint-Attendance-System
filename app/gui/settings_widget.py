from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QPushButton, QMessageBox, 
    QGroupBox, QTimeEdit, QSpinBox, QTableWidget, QHeaderView, QHBoxLayout,
    QTableWidgetItem, QAbstractItemView
)
from PyQt6.QtCore import QTime, QCoreApplication, pyqtSignal # <-- استيراد pyqtSignal
from PyQt6.QtGui import QFont
from app.database.database_manager import DatabaseManager
from app.utils.encryption import hash_password
from app.gui.user_dialog import UserDialog

class SettingsWidget(QWidget):
    """
    واجهة إعدادات شاملة للمدير.
    """
    # --- بداية الإضافة الجديدة: تعريف الإشارات ---
    theme_changed = pyqtSignal(str) # إشارة تحمل اسم الثيم الجديد
    language_changed = pyqtSignal(str) # إشارة تحمل كود اللغة الجديد
    # --- نهاية الإضافة الجديدة ---

    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.current_settings = {} # لتخزين الإعدادات الحالية
        self.setup_ui()
        self.connect_signals()
        self.load_settings()
        self.load_users_data()

    def setup_ui(self):
        # ... (نفس كود هذه الدالة بدون تغيير) ...
        layout = QVBoxLayout(self); appearance_group = QGroupBox(self.tr("Appearance & Language")); appearance_layout = QFormLayout(); self.theme_combo = QComboBox(); self.theme_combo.addItems(["light", "dark"]); appearance_layout.addRow(f"{self.tr('Application Theme')}:", self.theme_combo); self.lang_combo = QComboBox(); self.lang_combo.addItems(["en", "ar"]); appearance_layout.addRow(f"{self.tr('Interface Language')}:", self.lang_combo); appearance_group.setLayout(appearance_layout); layout.addWidget(appearance_group); work_group = QGroupBox(self.tr("Work Rules")); work_layout = QFormLayout(); self.start_time_edit = QTimeEdit(); self.start_time_edit.setDisplayFormat("hh:mm:ss ap"); work_layout.addRow(f"{self.tr('Official Work Start Time')}:", self.start_time_edit); self.late_allowance_spin = QSpinBox(); self.late_allowance_spin.setRange(0, 120); self.late_allowance_spin.setSuffix(f" {self.tr('minutes')}"); work_layout.addRow(f"{self.tr('Late Allowance Period')}:", self.late_allowance_spin); work_group.setLayout(work_layout); layout.addWidget(work_group); users_group = QGroupBox(self.tr("User Management")); users_layout = QVBoxLayout(); self.users_table = QTableWidget(); self.users_table.setColumnCount(3); self.users_table.setHorizontalHeaderLabels(["ID", self.tr("Username"), self.tr("Role")]); self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.users_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows); users_layout.addWidget(self.users_table); user_buttons_layout = QHBoxLayout(); self.add_user_button = QPushButton(f"➕ {self.tr('Add User')}"); self.delete_user_button = QPushButton(f"🗑️ {self.tr('Delete Selected User')}"); user_buttons_layout.addWidget(self.add_user_button); user_buttons_layout.addWidget(self.delete_user_button); user_buttons_layout.addStretch(); users_layout.addLayout(user_buttons_layout); users_group.setLayout(users_layout); layout.addWidget(users_group); self.save_button = QPushButton(f"💾 {self.tr('Save Settings')}"); self.save_button.setFont(QFont("Arial", 12)); layout.addWidget(self.save_button); layout.addStretch()

    def connect_signals(self):
        # ... (نفس كود هذه الدالة بدون تغيير) ...
        self.save_button.clicked.connect(self.save_settings); self.add_user_button.clicked.connect(self.add_user); self.delete_user_button.clicked.connect(self.delete_user)

    def load_settings(self):
        """Loads current settings from the database and displays them."""
        self.current_settings = self.db_manager.get_all_settings() # تخزين الإعدادات
        self.theme_combo.setCurrentText(self.current_settings.get('theme', 'light'))
        self.lang_combo.setCurrentText(self.current_settings.get('language', 'en'))
        start_time = QTime.fromString(self.current_settings.get('work_start_time', '08:30:00'), "HH:mm:ss")
        self.start_time_edit.setTime(start_time)
        self.late_allowance_spin.setValue(int(self.current_settings.get('late_allowance_minutes', 15)))

    def save_settings(self):
        """
        Saves the new settings and emits signals if theme or language have changed.
        """
        # --- بداية التعديل ---
        new_theme = self.theme_combo.currentText()
        new_lang = self.lang_combo.currentText()
        
        # حفظ الإعدادات الأخرى
        self.db_manager.save_setting('work_start_time', self.start_time_edit.time().toString("HH:mm:ss"))
        self.db_manager.save_setting('late_allowance_minutes', str(self.late_allowance_spin.value()))

        # التحقق من تغيير الثيم وإصدار الإشارة
        if new_theme != self.current_settings.get('theme'):
            self.db_manager.save_setting('theme', new_theme)
            self.theme_changed.emit(new_theme)

        # التحقق من تغيير اللغة وإصدار الإشارة
        if new_lang != self.current_settings.get('language'):
            self.db_manager.save_setting('language', new_lang)
            self.language_changed.emit(new_lang)
            QMessageBox.information(self, self.tr("Success"), self.tr("Settings saved. Language change requires a restart to take full effect."))
        else:
            QMessageBox.information(self, self.tr("Success"), self.tr("Settings saved successfully."))
        
        # تحديث الإعدادات الحالية
        self.load_settings()
        # --- نهاية التعديل ---

    # ... (باقي دوال الكلاس بدون تغيير) ...
    def load_users_data(self): users = self.db_manager.get_all_users(); self.users_table.setRowCount(0); self.users_table.setRowCount(len(users));
    def add_user(self): pass
    def delete_user(self): pass
    def tr(self, text): return QCoreApplication.translate("SettingsWidget", text)