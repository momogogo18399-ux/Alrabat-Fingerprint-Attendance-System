from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox, QPushButton, QMessageBox, 
    QGroupBox, QTimeEdit, QSpinBox
)
from PyQt6.QtCore import QTime, QCoreApplication, pyqtSignal
from PyQt6.QtGui import QFont
from app.database.database_manager import DatabaseManager

class SettingsWidget(QWidget):
    """
    واجهة إعدادات شاملة للمدير.
    تدير المظهر، قواعد العمل، ومستخدمي البرنامج.
    """
    # تعريف الإشارات التي سيتم إصدارها عند تغيير الإعدادات
    theme_changed = pyqtSignal(str) # إشارة تحمل اسم الثيم الجديد
    language_changed = pyqtSignal(str) # إشارة تحمل كود اللغة الجديد

    def __init__(self):
        super().__init__()
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

        # --- زر الحفظ ---
        self.save_button = QPushButton(f"💾 {self.tr('Save Settings')}")
        self.save_button.setFont(QFont("Arial", 12))
        layout.addWidget(self.save_button)
        layout.addStretch()
        
    def connect_signals(self):
        """تربط إشارة زر الحفظ بالدالة الخاصة بها."""
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
        تحفظ الإعدادات الجديدة وتصدر إشارات إذا تغير الثيم أو اللغة.
        """
        new_theme = self.theme_combo.currentText()
        new_lang = self.lang_combo.currentText()
        
        # حفظ الإعدادات الأخرى دائمًا
        self.db_manager.save_setting('work_start_time', self.start_time_edit.time().toString("HH:mm:ss"))
        self.db_manager.save_setting('late_allowance_minutes', str(self.late_allowance_spin.value()))

        lang_changed = new_lang != self.current_settings.get('language')

        # التحقق من تغيير الثيم وإصدار الإشارة
        if new_theme != self.current_settings.get('theme'):
            self.db_manager.save_setting('theme', new_theme)
            self.theme_changed.emit(new_theme)

        # التحقق من تغيير اللغة وإصدار الإشارة
        if lang_changed:
            self.db_manager.save_setting('language', new_lang)
            self.language_changed.emit(new_lang)
            # عرض رسالة خاصة للغة لأنها تتطلب إعادة بناء الواجهة
            QMessageBox.information(self, self.tr("Success"), self.tr("Settings saved. Language changes will be applied now."))
        else:
            QMessageBox.information(self, self.tr("Success"), self.tr("Settings saved successfully."))
        
        # تحديث الحالة الداخلية للإعدادات الحالية
        self.current_settings['theme'] = new_theme
        self.current_settings['language'] = new_lang

    def tr(self, text):
        """دالة مساعدة للترجمة."""
        return QCoreApplication.translate("SettingsWidget", text)