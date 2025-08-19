from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QMessageBox, QFrame, QSpinBox, QComboBox, QCheckBox,
    QTabWidget, QWidget, QFormLayout, QLineEdit, QColorDialog,
    QSlider, QGroupBox, QTextEdit, QFileDialog, QProgressDialog
)
from PyQt6.QtCore import Qt, QCoreApplication, pyqtSignal
from PyQt6.QtGui import QFont, QColor
import json
import os

class QRSettingsDialog(QDialog):
    """
    نافذة إعدادات احترافية لرموز QR
    """
    settings_changed = pyqtSignal(dict)  # إشارة عند تغيير الإعدادات
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.settings_file = "qr_settings.json"
        self.settings = self.load_settings()
        
        self.setWindowTitle("QR Code Settings")
        self.setMinimumSize(600, 500)
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # عنوان النافذة
        title_label = QLabel("⚙️ Professional QR Code Settings")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # تبويبات الإعدادات
        self.tab_widget = QTabWidget()
        
        # تبويب المظهر
        self.tab_widget.addTab(self.create_appearance_tab(), "🎨 Appearance")
        
        # تبويب الأمان
        self.tab_widget.addTab(self.create_security_tab(), "🔒 Security")
        
        # تبويب البيانات
        self.tab_widget.addTab(self.create_data_tab(), "📊 Data")
        
        # تبويب التصدير
        self.tab_widget.addTab(self.create_export_tab(), "📤 Export")
        
        layout.addWidget(self.tab_widget)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        
        self.reset_button = QPushButton("🔄 Reset")
        self.reset_button.clicked.connect(self.reset_settings)
        
        self.apply_all_button = QPushButton("🚀 Apply to All Codes")
        self.apply_all_button.setToolTip("Apply settings to all existing QR codes")
        self.apply_all_button.clicked.connect(self.apply_to_all_qr_codes)
        
        self.save_button = QPushButton("💾 Save Settings")
        self.save_button.clicked.connect(self.save_settings)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.apply_all_button)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def create_appearance_tab(self):
        """إنشاء تبويب المظهر"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # حجم الرمز
        self.size_spinbox = QSpinBox()
        self.size_spinbox.setRange(100, 1000)
        self.size_spinbox.setSuffix(" px")
        self.size_spinbox.setValue(self.settings.get('size', 300))
        layout.addRow("Size:", self.size_spinbox)
        
        # مستوى تصحيح الأخطاء
        self.error_correction_combo = QComboBox()
        self.error_correction_combo.addItems([
            "Low (7%)",
            "Medium (15%)",
            "High (25%)",
            "Highest (30%)"
        ])
        error_levels = ['L', 'M', 'Q', 'H']
        current_level = self.settings.get('error_correction', 'L')
        try:
            current_index = error_levels.index(current_level)
            self.error_correction_combo.setCurrentIndex(current_index)
        except ValueError:
            self.error_correction_combo.setCurrentIndex(0)  # افتراضي
        layout.addRow("Error Correction Level:", self.error_correction_combo)
        
        # حجم المربع
        self.box_size_spinbox = QSpinBox()
        self.box_size_spinbox.setRange(1, 20)
        self.box_size_spinbox.setValue(self.settings.get('box_size', 10))
        layout.addRow("Box Size:", self.box_size_spinbox)
        
        # حجم الحدود
        self.border_spinbox = QSpinBox()
        self.border_spinbox.setRange(0, 10)
        self.border_spinbox.setValue(self.settings.get('border', 4))
        layout.addRow("Border Size:", self.border_spinbox)
        
        # لون الخلفية
        self.background_color_button = QPushButton("Choose Color")
        self.background_color_button.clicked.connect(self.choose_background_color)
        layout.addRow("Background Color:", self.background_color_button)
        
        # لون الرمز
        self.foreground_color_button = QPushButton("Choose Color")
        self.foreground_color_button.clicked.connect(self.choose_foreground_color)
        layout.addRow("Foreground Color:", self.foreground_color_button)
        
        # إضافة شعار
        self.add_logo_checkbox = QCheckBox("Add Logo in the Middle")
        self.add_logo_checkbox.setChecked(self.settings.get('add_logo', False))
        layout.addRow(self.add_logo_checkbox)
        
        # مسار الشعار
        self.logo_path_edit = QLineEdit()
        self.logo_path_edit.setPlaceholderText("Choose Logo File...")
        self.logo_path_edit.setText(self.settings.get('logo_path', ''))
        
        self.logo_browse_button = QPushButton("Browse...")
        self.logo_browse_button.clicked.connect(self.browse_logo)
        
        logo_layout = QHBoxLayout()
        logo_layout.addWidget(self.logo_path_edit)
        logo_layout.addWidget(self.logo_browse_button)
        layout.addRow("Logo Path:", logo_layout)
        
        return widget
    
    def create_security_tab(self):
        """إنشاء تبويب الأمان"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # تشفير البيانات
        self.encrypt_data_checkbox = QCheckBox("Encrypt Data")
        self.encrypt_data_checkbox.setChecked(self.settings.get('encrypt_data', True))
        layout.addRow(self.encrypt_data_checkbox)
        
        # مفتاح التشفير
        self.encryption_key_edit = QLineEdit()
        self.encryption_key_edit.setPlaceholderText("Encryption Key (leave empty for auto-generation)")
        self.encryption_key_edit.setText(self.settings.get('encryption_key', ''))
        layout.addRow("Encryption Key:", self.encryption_key_edit)
        
        # فترة الصلاحية
        self.expiry_spinbox = QSpinBox()
        self.expiry_spinbox.setRange(1, 365)
        self.expiry_spinbox.setSuffix(" days")
        self.expiry_spinbox.setValue(self.settings.get('expiry_days', 30))
        layout.addRow("Expiry Period:", self.expiry_spinbox)
        
        # التحقق من الموقع
        self.location_verification_checkbox = QCheckBox("Location Verification")
        self.location_verification_checkbox.setChecked(self.settings.get('location_verification', False))
        layout.addRow(self.location_verification_checkbox)
        
        # نطاق الموقع (بالأمتار)
        self.location_radius_spinbox = QSpinBox()
        self.location_radius_spinbox.setRange(10, 10000)
        self.location_radius_spinbox.setSuffix(" meters")
        self.location_radius_spinbox.setValue(self.settings.get('location_radius', 100))
        layout.addRow("Location Radius:", self.location_radius_spinbox)
        
        # التحقق من الوقت
        self.time_verification_checkbox = QCheckBox("Time Verification")
        self.time_verification_checkbox.setChecked(self.settings.get('time_verification', True))
        layout.addRow(self.time_verification_checkbox)
        
        # نطاق الوقت المسموح
        self.time_window_spinbox = QSpinBox()
        self.time_window_spinbox.setRange(1, 24)
        self.time_window_spinbox.setSuffix(" hours")
        self.time_window_spinbox.setValue(self.settings.get('time_window', 2))
        layout.addRow("Time Window:", self.time_window_spinbox)
        
        return widget
    
    def create_data_tab(self):
        """إنشاء تبويب البيانات"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # البيانات الأساسية
        self.include_employee_id_checkbox = QCheckBox("Employee ID")
        self.include_employee_id_checkbox.setChecked(self.settings.get('include_employee_id', True))
        layout.addRow(self.include_employee_id_checkbox)
        
        self.include_employee_code_checkbox = QCheckBox("Employee Code")
        self.include_employee_code_checkbox.setChecked(self.settings.get('include_employee_code', True))
        layout.addRow(self.include_employee_code_checkbox)
        
        self.include_name_checkbox = QCheckBox("Employee Name")
        self.include_name_checkbox.setChecked(self.settings.get('include_name', False))
        layout.addRow(self.include_name_checkbox)
        
        self.include_department_checkbox = QCheckBox("Department")
        self.include_department_checkbox.setChecked(self.settings.get('include_department', False))
        layout.addRow(self.include_department_checkbox)
        
        self.include_timestamp_checkbox = QCheckBox("Timestamp")
        self.include_timestamp_checkbox.setChecked(self.settings.get('include_timestamp', True))
        layout.addRow(self.include_timestamp_checkbox)
        
        # تنسيق التاريخ
        self.date_format_combo = QComboBox()
        self.date_format_combo.addItems([
            "YYYY-MM-DD HH:MM:SS",
            "DD/MM/YYYY HH:MM",
            "MM/DD/YYYY HH:MM",
            "Unix Timestamp"
        ])
        date_formats = ['%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M', '%m/%d/%Y %H:%M', 'unix']
        current_format = self.settings.get('date_format', '%Y-%m-%d %H:%M:%S')
        try:
            current_index = date_formats.index(current_format)
            self.date_format_combo.setCurrentIndex(current_index)
        except ValueError:
            self.date_format_combo.setCurrentIndex(0)  # افتراضي
        layout.addRow("Date Format:", self.date_format_combo)
        
        # بيانات إضافية
        self.additional_data_edit = QTextEdit()
        self.additional_data_edit.setMaximumHeight(80)
        self.additional_data_edit.setPlaceholderText("Enter additional data (JSON format)")
        self.additional_data_edit.setText(self.settings.get('additional_data', ''))
        layout.addRow("Additional Data:", self.additional_data_edit)
        
        return widget
    
    def create_export_tab(self):
        """إنشاء تبويب التصدير"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # تنسيق التصدير
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(["PNG", "JPEG", "SVG", "PDF"])
        self.export_format_combo.setCurrentText(self.settings.get('export_format', 'PNG'))
        layout.addRow("Export Format:", self.export_format_combo)
        
        # جودة الصورة
        self.image_quality_slider = QSlider(Qt.Orientation.Horizontal)
        self.image_quality_slider.setRange(1, 100)
        self.image_quality_slider.setValue(self.settings.get('image_quality', 95))
        self.image_quality_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.image_quality_slider.setTickInterval(10)
        layout.addRow("Image Quality:", self.image_quality_slider)
        
        # دقة الصورة
        self.dpi_spinbox = QSpinBox()
        self.dpi_spinbox.setRange(72, 600)
        self.dpi_spinbox.setSuffix(" DPI")
        self.dpi_spinbox.setValue(self.settings.get('dpi', 300))
        layout.addRow("DPI:", self.dpi_spinbox)
        
        # مجلد التصدير الافتراضي
        self.export_folder_edit = QLineEdit()
        self.export_folder_edit.setText(self.settings.get('export_folder', os.path.expanduser("~/Desktop")))
        
        self.export_folder_browse_button = QPushButton("Browse...")
        self.export_folder_browse_button.clicked.connect(self.browse_export_folder)
        
        export_folder_layout = QHBoxLayout()
        export_folder_layout.addWidget(self.export_folder_edit)
        export_folder_layout.addWidget(self.export_folder_browse_button)
        layout.addRow("Export Folder:", export_folder_layout)
        
        # تسمية الملفات
        self.file_naming_combo = QComboBox()
        self.file_naming_combo.addItems([
            "qr_code_{employee_code}",
            "qr_{employee_name}_{date}",
            "employee_{id}_qr",
            "custom"
        ])
        self.file_naming_combo.setCurrentText(self.settings.get('file_naming', 'qr_code_{employee_code}'))
        layout.addRow("File Naming:", self.file_naming_combo)
        
        # تسمية مخصصة
        self.custom_filename_edit = QLineEdit()
        self.custom_filename_edit.setPlaceholderText("Example: qr_{employee_code}_{timestamp}")
        self.custom_filename_edit.setText(self.settings.get('custom_filename', ''))
        layout.addRow("Custom Filename:", self.custom_filename_edit)
        
        return widget
    
    def choose_background_color(self):
        """اختيار لون الخلفية"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.settings['background_color'] = color.name()
            self.background_color_button.setStyleSheet(f"background-color: {color.name()}; color: white;")
    
    def choose_foreground_color(self):
        """اختيار لون الرمز"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.settings['foreground_color'] = color.name()
            self.foreground_color_button.setStyleSheet(f"background-color: {color.name()}; color: white;")
    
    def browse_logo(self):
        """تصفح ملف الشعار"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose Logo File",
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        if file_path:
            self.logo_path_edit.setText(file_path)
            self.settings['logo_path'] = file_path
    
    def browse_export_folder(self):
        """تصفح مجلد التصدير"""
        folder_path = QFileDialog.getExistingDirectory(
            self,
            "Choose Export Folder"
        )
        if folder_path:
            self.export_folder_edit.setText(folder_path)
            self.settings['export_folder'] = folder_path
    
    def load_current_settings(self):
        """تحميل الإعدادات الحالية"""
        # تحديث ألوان الأزرار
        if 'background_color' in self.settings:
            self.background_color_button.setStyleSheet(f"background-color: {self.settings['background_color']}; color: white;")
        
        if 'foreground_color' in self.settings:
            self.foreground_color_button.setStyleSheet(f"background-color: {self.settings['foreground_color']}; color: white;")
    
    def get_current_settings(self):
        """الحصول على الإعدادات الحالية من الواجهة"""
        settings = {}
        
        # إعدادات المظهر
        settings['size'] = self.size_spinbox.value()
        error_levels = ['L', 'M', 'Q', 'H']
        settings['error_correction'] = error_levels[self.error_correction_combo.currentIndex()]
        settings['box_size'] = self.box_size_spinbox.value()
        settings['border'] = self.border_spinbox.value()
        settings['add_logo'] = self.add_logo_checkbox.isChecked()
        settings['logo_path'] = self.logo_path_edit.text()
        
        # إعدادات الأمان
        settings['encrypt_data'] = self.encrypt_data_checkbox.isChecked()
        settings['encryption_key'] = self.encryption_key_edit.text()
        settings['expiry_days'] = self.expiry_spinbox.value()
        settings['location_verification'] = self.location_verification_checkbox.isChecked()
        settings['location_radius'] = self.location_radius_spinbox.value()
        settings['time_verification'] = self.time_verification_checkbox.isChecked()
        settings['time_window'] = self.time_window_spinbox.value()
        
        # إعدادات البيانات
        settings['include_employee_id'] = self.include_employee_id_checkbox.isChecked()
        settings['include_employee_code'] = self.include_employee_code_checkbox.isChecked()
        settings['include_name'] = self.include_name_checkbox.isChecked()
        settings['include_department'] = self.include_department_checkbox.isChecked()
        settings['include_timestamp'] = self.include_timestamp_checkbox.isChecked()
        
        date_formats = ['%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M', '%m/%d/%Y %H:%M', 'unix']
        settings['date_format'] = date_formats[self.date_format_combo.currentIndex()]
        settings['additional_data'] = self.additional_data_edit.toPlainText()
        
        # إعدادات التصدير
        settings['export_format'] = self.export_format_combo.currentText()
        settings['image_quality'] = self.image_quality_slider.value()
        settings['dpi'] = self.dpi_spinbox.value()
        settings['export_folder'] = self.export_folder_edit.text()
        settings['file_naming'] = self.file_naming_combo.currentText()
        settings['custom_filename'] = self.custom_filename_edit.text()
        
        return settings
    
    def load_settings(self):
        """تحميل الإعدادات من الملف"""
        default_settings = {
            'size': 300,
            'error_correction': 'L',
            'box_size': 10,
            'border': 4,
            'background_color': '#FFFFFF',
            'foreground_color': '#000000',
            'add_logo': False,
            'logo_path': '',
            'encrypt_data': True,
            'encryption_key': '',
            'expiry_days': 30,
            'location_verification': False,
            'location_radius': 100,
            'time_verification': True,
            'time_window': 2,
            'include_employee_id': True,
            'include_employee_code': True,
            'include_name': False,
            'include_department': False,
            'include_timestamp': True,
            'date_format': '%Y-%m-%d %H:%M:%S',
            'additional_data': '',
            'export_format': 'PNG',
            'image_quality': 95,
            'dpi': 300,
            'export_folder': os.path.expanduser("~/Desktop"),
            'file_naming': 'qr_code_{employee_code}',
            'custom_filename': ''
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # دمج الإعدادات المحملة مع الإعدادات الافتراضية
                    for key, value in loaded_settings.items():
                        if key in default_settings:
                            default_settings[key] = value
        except Exception as e:
            print(f"خطأ في تحميل إعدادات QR: {e}")
        
        return default_settings
    
    def save_settings(self):
        """حفظ الإعدادات"""
        try:
            current_settings = self.get_current_settings()
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(current_settings, f, ensure_ascii=False, indent=2)
            
            self.settings = current_settings
            self.settings_changed.emit(current_settings)
            
            QMessageBox.information(self, "Success", "Settings saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings:\n{str(e)}")
    
    def reset_settings(self):
        """إعادة تعيين الإعدادات"""
        reply = QMessageBox.question(
            self,
            "Confirm Reset",
            "Do you want to reset all settings to default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.settings = self.load_settings()
            self.load_current_settings()
            QMessageBox.information(self, "Success", "Settings reset!")
    
    def apply_to_all_qr_codes(self):
        """تطبيق الإعدادات على جميع رموز QR الموجودة"""
        try:
            from app.database.database_manager import DatabaseManager
            from app.utils.qr_manager import QRCodeManager
            
            db_manager = DatabaseManager()
            qr_manager = QRCodeManager()
            
            # الحصول على جميع الموظفين
            employees = db_manager.get_all_employees()
            
            if not employees:
                QMessageBox.information(self, "Information", 
                                      "No employees found in the system.")
                return
            
            # تأكيد العملية
            reply = QMessageBox.question(
                self,
                "Confirm Application",
                f"Do you want to apply the new settings to all QR codes ({len(employees)} employees)?\n\nThis process may take some time.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # إظهار شريط التقدم
                progress_dialog = QProgressDialog(
                    "Applying settings to all QR codes...", 
                    "Cancel", 0, len(employees), self
                )
                progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
                progress_dialog.setAutoClose(False)
                progress_dialog.show()
                
                success_count = 0
                error_count = 0
                
                for i, employee in enumerate(employees):
                    progress_dialog.setValue(i)
                    progress_dialog.setLabelText(
                        f"Updating QR code for employee: {employee.get('name', 'Unknown')}"
                    )
                    
                    # التحقق من إلغاء العملية
                    if progress_dialog.wasCanceled():
                        break
                    
                    try:
                        # تحديث إعدادات QR Manager
                        qr_manager.update_settings(self.get_current_settings())
                        
                        # إنشاء رمز QR جديد مع الإعدادات الجديدة
                        qr_code = qr_manager.generate_qr_code(employee)
                        if qr_code:
                            # حفظ الرمز الجديد
                            db_manager.update_employee_qr_code(employee['id'], qr_code)
                            success_count += 1
                        else:
                            error_count += 1
                            
                    except Exception as e:
                        error_count += 1
                        print(f"❌ Failed to update QR code for employee {employee.get('name')}: {e}")
                    
                    # تحديث واجهة المستخدم
                    QCoreApplication.processEvents()
                
                progress_dialog.setValue(len(employees))
                progress_dialog.close()
                
                # عرض النتائج
                result_message = f"Settings applied successfully!\n\n"
                result_message += f"✅ Success: {success_count}\n"
                if error_count > 0:
                    result_message += f"❌ Failed: {error_count}"
                
                QMessageBox.information(self, "Success", result_message)
                
                # إرسال إشارة تحديث الإعدادات
                self.settings_changed.emit(self.get_current_settings())
                
        except Exception as e:
            QMessageBox.critical(self, "Error", 
                               f"Failed to apply settings:\n{str(e)}")
    
    def tr(self, text):
        return QCoreApplication.translate("QRSettingsDialog", text)
