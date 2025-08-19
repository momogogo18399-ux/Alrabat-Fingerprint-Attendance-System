from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, 
    QMessageBox, QFrame, QSizePolicy, QFileDialog
)
from PyQt6.QtCore import Qt, QCoreApplication
from PyQt6.QtGui import QPixmap, QFont
from app.utils.qr_manager import QRCodeManager
from app.database.database_manager import DatabaseManager

class QRCodeDialog(QDialog):
    """
    نافذة حوار لعرض رمز QR للموظف
    """
    def __init__(self, employee_data, parent=None):
        super().__init__(parent)
        
        self.employee_data = employee_data
        self.qr_manager = QRCodeManager()
        self.db_manager = DatabaseManager()
        
        self.setWindowTitle(self.tr("QR Code - {name}").format(name=employee_data.get('name', '')))
        self.setMinimumSize(400, 500)
        self.setup_ui()
        self.generate_qr_code()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # عنوان النافذة
        title_label = QLabel(self.tr("QR Code for Employee"))
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # معلومات الموظف
        info_frame = QFrame()
        info_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        info_layout = QVBoxLayout(info_frame)
        
        name_label = QLabel(f"{self.tr('Name')}: {self.employee_data.get('name', '')}")
        code_label = QLabel(f"{self.tr('Code')}: {self.employee_data.get('employee_code', '')}")
        dept_label = QLabel(f"{self.tr('Department')}: {self.employee_data.get('department', '')}")
        
        for label in [name_label, code_label, dept_label]:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            info_layout.addWidget(label)
        
        layout.addWidget(info_frame)
        
        # منطقة عرض QR Code
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.qr_label.setMinimumSize(300, 300)
        self.qr_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.qr_label.setStyleSheet("border: 2px solid #ccc; border-radius: 10px;")
        layout.addWidget(self.qr_label)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton(self.tr("Save QR Code"))
        self.save_button.setToolTip(self.tr("Save QR code image to file"))
        self.save_button.clicked.connect(self.save_qr_code)
        
        self.refresh_button = QPushButton(self.tr("Refresh QR Code"))
        self.refresh_button.setToolTip(self.tr("Generate new QR code"))
        self.refresh_button.clicked.connect(self.refresh_qr_code)
        
        self.close_button = QPushButton(self.tr("Close"))
        self.close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
    
    def generate_qr_code(self):
        """إنشاء رمز QR للموظف"""
        try:
            # التحقق من وجود رمز QR في قاعدة البيانات
            employee_id = self.employee_data.get('id')
            if employee_id:
                employee = self.db_manager.get_employee_by_id(employee_id)
                if employee and employee.get('qr_code'):
                    # الرمز موجود بالفعل
                    qr_code = employee['qr_code']
                    print(f"استخدام الرمز الموجود للموظف: {employee.get('name')}")
                else:
                    # إنشاء رمز جديد
                    qr_code = self.qr_manager.generate_qr_code(self.employee_data)
                    if qr_code:
                        self.db_manager.update_employee_qr_code(employee_id, qr_code)
                        print(f"تم إنشاء رمز QR جديد للموظف: {self.employee_data.get('name')}")
                    else:
                        raise Exception("فشل في إنشاء رمز QR")
            else:
                raise Exception("لم يتم العثور على بيانات الموظف")
            
            # إنشاء صورة QR Code
            qr_pixmap = self.qr_manager.create_qr_image(qr_code, 300)
            self.qr_label.setPixmap(qr_pixmap)
            
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                               f"{self.tr('Failed to generate QR code:')}\n{str(e)}")
    
    def refresh_qr_code(self):
        """تحديث رمز QR"""
        reply = QMessageBox.question(
            self, 
            self.tr("Refresh QR Code"), 
            self.tr("This will generate a new QR code. The old one will become invalid. Continue?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.generate_qr_code()
    
    def save_qr_code(self):
        """حفظ رمز QR كصورة"""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                self.tr("Save QR Code"),
                f"qr_code_{self.employee_data.get('employee_code', 'employee')}.png",
                "PNG Files (*.png);;All Files (*)"
            )
            
            if file_path:
                # الحصول على الرمز الحالي من قاعدة البيانات
                employee_id = self.employee_data.get('id')
                if employee_id:
                    employee = self.db_manager.get_employee_by_id(employee_id)
                    if employee and employee.get('qr_code'):
                        success = self.qr_manager.save_qr_image(employee['qr_code'], file_path)
                        if success:
                            QMessageBox.information(self, self.tr("Success"), 
                                                   self.tr("QR code saved successfully!"))
                        else:
                            QMessageBox.critical(self, self.tr("Error"), 
                                               self.tr("Failed to save QR code image."))
                    else:
                        QMessageBox.warning(self, self.tr("Warning"), 
                                          self.tr("No QR code found for this employee."))
                        
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                               f"{self.tr('Failed to save QR code:')}\n{str(e)}")
