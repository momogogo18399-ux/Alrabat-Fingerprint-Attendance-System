from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QMessageBox, QFileDialog, QFrame, QTextEdit, QLineEdit
)
from PyQt6.QtCore import Qt, QCoreApplication, QTimer
from PyQt6.QtGui import QPixmap, QFont, QImage
from app.utils.qr_manager import QRCodeManager
from app.database.database_manager import DatabaseManager
import cv2
from pyzbar import pyzbar
import numpy as np

class QRScannerDialog(QDialog):
    """
    Dialog window for scanning QR codes للموظفين
    """
    def __init__(self, db_manager=None, parent=None):
        super().__init__(parent)
        
        self.qr_manager = QRCodeManager()
        self.db_manager = db_manager or DatabaseManager()
        self.camera = None
        self.scanning = False
        
        self.setWindowTitle(self.tr("QR Code Scanner"))
        self.setMinimumSize(600, 500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # عنوان النافذة
        title_label = QLabel(self.tr("QR Code Scanner"))
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # منطقة عرض الكاميرا
        self.camera_label = QLabel()
        self.camera_label.setMinimumSize(400, 300)
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setStyleSheet("border: 2px solid #ccc; border-radius: 10px; background-color: #f0f0f0;")
        self.camera_label.setText(self.tr("Camera not started"))
        layout.addWidget(self.camera_label)
        
        # منطقة إدخال رمز QR يدوياً
        manual_frame = QFrame()
        manual_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        manual_layout = QVBoxLayout(manual_frame)
        
        manual_label = QLabel(self.tr("Or enter QR code manually:"))
        manual_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        manual_layout.addWidget(manual_label)
        
        self.manual_input = QLineEdit()
        self.manual_input.setPlaceholderText(self.tr("Enter QR code here..."))
        self.manual_input.returnPressed.connect(self.process_manual_input)
        manual_layout.addWidget(self.manual_input)
        
        layout.addWidget(manual_frame)
        
        # منطقة عرض النتائج
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(100)
        self.result_text.setReadOnly(True)
        self.result_text.setPlaceholderText(self.tr("Scan results will appear here..."))
        layout.addWidget(self.result_text)
        
        # أزرار التحكم
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton(self.tr("Start Camera"))
        self.start_button.clicked.connect(self.toggle_camera)
        
        self.scan_file_button = QPushButton(self.tr("Scan from File"))
        self.scan_file_button.clicked.connect(self.scan_from_file)
        
        self.clear_button = QPushButton(self.tr("Clear Results"))
        self.clear_button.clicked.connect(self.clear_results)
        
        self.close_button = QPushButton(self.tr("Close"))
        self.close_button.clicked.connect(self.close)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.scan_file_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addStretch()
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        # مؤقت لUpdate الكاميرا
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_camera)
    
    def toggle_camera(self):
        """تشغيل/إيقاف الكاميرا"""
        if not self.scanning:
            self.start_camera()
        else:
            self.stop_camera()
    
    def start_camera(self):
        """تشغيل الكاميرا"""
        try:
            self.camera = cv2.VideoCapture(0)
            if not self.camera.isOpened():
                QMessageBox.warning(self, self.tr("Warning"), 
                                  self.tr("Could not open camera. Please check if camera is connected."))
                return
            
            self.scanning = True
            self.start_button.setText(self.tr("Stop Camera"))
            self.timer.start(30)  # 30ms = ~33 FPS
            
        except Exception as e:
            QMessageBox.critical(self, self.tr("Error"), 
                               f"{self.tr('Failed to start camera:')}\n{str(e)}")
    
    def stop_camera(self):
        """إيقاف الكاميرا"""
        self.scanning = False
        self.start_button.setText(self.tr("Start Camera"))
        self.timer.stop()
        
        if self.camera:
            self.camera.release()
            self.camera = None
        
        self.camera_label.setText(self.tr("Camera stopped"))
    
    def update_camera(self):
        """Update إطار الكاميرا"""
        if not self.scanning or not self.camera:
            return
        
        ret, frame = self.camera.read()
        if not ret:
            return
        
        # الSearch عن رموز QR في الإطار
        qr_codes = self.detect_qr_codes(frame)
        
        # رسم مربعات حول رموز QR المكتشفة
        for qr_code in qr_codes:
            points = qr_code.polygon
            if len(points) > 4:
                hull = cv2.convexHull(np.array([point for point in points], dtype=np.float32))
                points = hull
            
            n = len(points)
            for j in range(n):
                cv2.line(frame, tuple(points[j]), tuple(points[(j + 1) % n]), (0, 255, 0), 3)
            
            # معالجة رمز QR المكتشف
            self.process_qr_code(qr_code.data.decode('utf-8'))
        
        # تحويل الإطار إلى QPixmap
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_frame.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_frame.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        
        # تغيير حجم الصورة لتناسب العرض
        scaled_pixmap = pixmap.scaled(self.camera_label.size(), Qt.AspectRatioMode.KeepAspectRatio)
        self.camera_label.setPixmap(scaled_pixmap)
    
    def detect_qr_codes(self, frame):
        """اكتشاف رموز QR في الإطار"""
        try:
            qr_codes = pyzbar.decode(frame)
            return qr_codes
        except Exception as e:
            print(f"Error detecting QR codes: {e}")
            return []
    
    def process_qr_code(self, qr_data):
        """معالجة رمز QR المكتشف"""
        try:
            # التحقق من صحة الرمز
            result = self.qr_manager.verify_qr_code(qr_data)
            
            if result and result.get('is_valid'):
                employee_id = result.get('employee_id')
                employee = self.db_manager.get_employee_by_id(employee_id)
                
                if employee:
                    # تسجيل الحضور
                    self.record_attendance(employee)
                else:
                    self.add_result(f"❌ {self.tr('Employee not found')}: {employee_id}")
            else:
                self.add_result(f"❌ {self.tr('Invalid QR code')}: {qr_data[:50]}...")
                
        except Exception as e:
            self.add_result(f"❌ {self.tr('Error processing QR code')}: {str(e)}")
    
    def process_manual_input(self):
        """معالجة الإدخال اليدوي لرمز QR"""
        qr_data = self.manual_input.text().strip()
        if qr_data:
            self.process_qr_code(qr_data)
            self.manual_input.clear()
    
    def scan_from_file(self):
        """مسح رمز QR من ملف صورة"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Select QR Code Image"),
            "",
            "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)"
        )
        
        if file_path:
            try:
                # قراءة الصورة
                image = cv2.imread(file_path)
                if image is None:
                    QMessageBox.warning(self, self.tr("Warning"), 
                                      self.tr("Could not read the image file."))
                    return
                
                # اكتشاف رموز QR
                qr_codes = self.detect_qr_codes(image)
                
                if qr_codes:
                    for qr_code in qr_codes:
                        self.process_qr_code(qr_code.data.decode('utf-8'))
                else:
                    QMessageBox.information(self, self.tr("No QR Code Found"), 
                                          self.tr("No QR code was detected in the selected image."))
                    
            except Exception as e:
                QMessageBox.critical(self, self.tr("Error"), 
                                   f"{self.tr('Failed to scan image:')}\n{str(e)}")
    
    def record_attendance(self, employee):
        """تسجيل الحضور للموظف"""
        try:
            from datetime import datetime
            
            current_time = datetime.now()
            current_date = current_time.strftime('%Y-%m-%d')
            current_time_str = current_time.strftime('%H:%M:%S')
            
            # التحقق من وجود تسجيل حضور اليوم
            existing_attendance = self.db_manager.get_attendance_by_employee_date(
                employee['id'], current_date
            )
            
            if existing_attendance:
                # إذا كان هناك تسجيل حضور، سجل انصراف
                attendance_type = 'check_out'
                message = f"✅ {self.tr('Check-out recorded for')}: {employee['name']} at {current_time_str}"
            else:
                # إذا لم يكن هناك تسجيل حضور، سجل حضور
                attendance_type = 'check_in'
                message = f"✅ {self.tr('Check-in recorded for')}: {employee['name']} at {current_time_str}"
            
            # Add تسجيل الحضور
            if hasattr(self.db_manager, 'record_attendance') and hasattr(self.db_manager, '_immediate_sync'):
                # استخدام النظام الهجين
                attendance_data = {
                    'employee_id': employee['id'],
                    'check_time': current_time_str,
                    'date': current_date,
                    'type': attendance_type,
                    'notes': 'QR Code scan'
                }
                result = self.db_manager.record_attendance(attendance_data)
            else:
                # استخدام النظام التقليدي
                attendance_data = {
                    'employee_id': employee['id'],
                    'check_time': current_time_str,
                    'date': current_date,
                    'type': attendance_type,
                    'notes': 'QR Code scan'
                }
                result = self.db_manager.add_attendance(attendance_data)
            
            if result:
                self.add_result(message)
            else:
                self.add_result(f"❌ {self.tr('Failed to record attendance')}: Unknown error")
            
        except Exception as e:
            self.add_result(f"❌ {self.tr('Failed to record attendance')}: {str(e)}")
    
    def add_result(self, message):
        """Add رسالة إلى منطقة النتائج"""
        from datetime import datetime
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.result_text.append(f"[{timestamp}] {message}")
    
    def clear_results(self):
        """مسح النتائج"""
        self.result_text.clear()
    
    def closeEvent(self, event):
        """معالجة Close النافذة"""
        self.stop_camera()
        event.accept()
