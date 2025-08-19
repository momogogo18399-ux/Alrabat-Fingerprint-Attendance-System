import qrcode
import base64
import hashlib
import secrets
import json
from datetime import datetime
from typing import Optional, Dict, Any
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt
import io
import os

class QRCodeManager:
    """
    نظام إدارة رموز QR للموظفين
    يقوم بإنشاء رموز QR مشفرة وفريدة لكل موظف
    """
    
    def __init__(self):
        """تهيئة مدير رموز QR"""
        self.settings = self.load_settings()
    
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
            'encrypt_data': False,  # تم تعطيل التشفير حالياً
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
            'date_format': '%Y%m%d%H%M%S',
            'additional_data': '',
            'export_format': 'PNG',
            'image_quality': 95,
            'dpi': 300,
            'export_folder': '',
            'file_naming': 'qr_code_{employee_code}',
            'custom_filename': ''
        }
        
        try:
            if os.path.exists('qr_settings.json'):
                with open('qr_settings.json', 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # دمج الإعدادات المحملة مع الإعدادات الافتراضية
                    for key, value in loaded_settings.items():
                        if key in default_settings:
                            default_settings[key] = value
        except Exception as e:
            print(f"خطأ في تحميل إعدادات QR: {e}")
        
        return default_settings
    
    def update_settings(self, new_settings):
        """تحديث الإعدادات"""
        self.settings.update(new_settings)
    
    def _generate_secret_key(self) -> str:
        """إنشاء مفتاح سري عشوائي"""
        return secrets.token_hex(32)
    
    def _encrypt_data(self, data: str) -> str:
        """
        تشفير البيانات باستخدام المفتاح السري
        :param data: البيانات المراد تشفيرها
        :return: البيانات المشفرة
        """
        # استخدام hash للمفتاح السري مع البيانات
        combined = f"{self.settings.get('encryption_key', self._generate_secret_key())}:{data}"
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def _decrypt_data(self, encrypted_data: str, original_data: str) -> bool:
        """
        التحقق من صحة البيانات المشفرة
        :param encrypted_data: البيانات المشفرة
        :param original_data: البيانات الأصلية
        :return: True إذا كانت البيانات صحيحة
        """
        expected_encrypted = self._encrypt_data(original_data)
        return encrypted_data == expected_encrypted
    
    def generate_qr_code(self, employee_data: Dict[str, Any]) -> str:
        """
        إنشاء رمز QR مبسط للموظف
        :param employee_data: بيانات الموظف
        :return: رمز QR مبسط
        """
        # إنشاء معرف فريد للموظف
        employee_id = str(employee_data.get('id', ''))
        employee_code = employee_data.get('employee_code', '')
        
        # استخدام تنسيق التاريخ من الإعدادات
        date_format = self.settings.get('date_format', '%Y%m%d%H%M%S')
        timestamp = datetime.now().strftime(date_format)
        
        # بناء البيانات حسب الإعدادات
        qr_parts = []
        
        if self.settings.get('include_employee_id', True):
            qr_parts.append(f"ID:{employee_id}")
        
        if self.settings.get('include_employee_code', True):
            qr_parts.append(f"CODE:{employee_code}")
        
        if self.settings.get('include_name', False):
            employee_name = employee_data.get('name', '')
            # تحويل النص العربي إلى Base64 لتجنب مشاكل التشفير
            if employee_name:
                try:
                    encoded_name = base64.b64encode(employee_name.encode('utf-8')).decode('ascii')
                    qr_parts.append(f"NAME:{encoded_name}")
                except:
                    qr_parts.append(f"NAME:{employee_name}")
        
        if self.settings.get('include_department', False):
            department = employee_data.get('department', '')
            if department:
                try:
                    encoded_dept = base64.b64encode(department.encode('utf-8')).decode('ascii')
                    qr_parts.append(f"DEPT:{encoded_dept}")
                except:
                    qr_parts.append(f"DEPT:{department}")
        
        if self.settings.get('include_timestamp', True):
            qr_parts.append(f"TIME:{timestamp}")
        
        # إضافة بيانات إضافية إذا كانت موجودة
        additional_data = self.settings.get('additional_data', '')
        if additional_data:
            try:
                # محاولة تحليل JSON
                import json
                parsed_data = json.loads(additional_data)
                for key, value in parsed_data.items():
                    qr_parts.append(f"{key}:{value}")
            except:
                # إذا فشل التحليل، أضف النص كما هو
                qr_parts.append(f"EXTRA:{additional_data}")
        
        # إنشاء الرمز النهائي
        if qr_parts:
            qr_code = "|".join(qr_parts)
        else:
            # إذا لم يتم تحديد أي بيانات، استخدم التنسيق الأساسي
            qr_code = f"EMP:{employee_id}:{employee_code}:{timestamp}"
        
        return qr_code
    
    def create_qr_image(self, qr_code: str, size: int = None) -> QPixmap:
        """
        إنشاء صورة رمز QR
        :param qr_code: رمز QR
        :param size: حجم الصورة (اختياري)
        :return: صورة QPixmap
        """
        try:
            # استخدام الحجم من الإعدادات إذا لم يتم تحديده
            if size is None:
                size = self.settings.get('size', 300)
            
            # إنشاء رمز QR مع الإعدادات
            qr = qrcode.QRCode(
                version=1,
                error_correction=getattr(qrcode.constants, f'ERROR_CORRECT_{self.settings.get("error_correction", "L")}'),
                box_size=self.settings.get('box_size', 10),
                border=self.settings.get('border', 4)
            )
            
            # تحويل النص إلى UTF-8 bytes ثم إلى base64 لتجنب مشاكل التشفير
            try:
                safe_qr_code = base64.b64encode(qr_code.encode('utf-8')).decode('ascii')
                qr.add_data(safe_qr_code)
            except:
                # إذا فشل، استخدم النص الأصلي
                qr.add_data(qr_code)
            qr.make(fit=True)
            
            # إنشاء الصورة
            img = qr.make_image(
                fill_color=self.settings.get('foreground_color', '#000000'),
                back_color=self.settings.get('background_color', '#FFFFFF')
            )
            
            # إضافة شعار إذا كان مفعلاً
            if self.settings.get('add_logo') and self.settings.get('logo_path'):
                img = self.add_logo_to_qr(img, self.settings['logo_path'])
            
            # تحويل إلى QPixmap
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            
            pixmap = QPixmap()
            pixmap.loadFromData(img_byte_arr)
            
            # تغيير الحجم إذا لزم الأمر
            if pixmap.width() != size:
                pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            
            return pixmap
            
        except Exception as e:
            print(f"خطأ في إنشاء صورة QR: {e}")
            # إنشاء صورة خطأ بسيطة
            from PyQt6.QtGui import QColor
            error_pixmap = QPixmap(size, size)
            error_pixmap.fill(QColor(255, 255, 255))  # أبيض
            return error_pixmap
    
    def save_qr_image(self, qr_code: str, file_path: str) -> bool:
        """
        حفظ رمز QR كصورة
        :param qr_code: رمز QR
        :param file_path: مسار الملف للحفظ
        :return: True إذا تم الحفظ بنجاح
        """
        try:
            # إنشاء صورة QR
            qr_pixmap = self.create_qr_image(qr_code, 300)
            
            # حفظ الصورة
            success = qr_pixmap.save(file_path, "PNG")
            return success
            
        except Exception as e:
            print(f"خطأ في حفظ صورة QR: {e}")
            return False
    
    def add_logo_to_qr(self, qr_img, logo_path):
        """إضافة شعار إلى رمز QR"""
        try:
            from PIL import Image
            
            # فتح الشعار
            logo = Image.open(logo_path)
            
            # تغيير حجم الشعار (20% من حجم QR)
            logo_size = int(qr_img.size[0] * 0.2)
            logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
            
            # حساب الموقع المركزي
            pos = ((qr_img.size[0] - logo_size) // 2, (qr_img.size[1] - logo_size) // 2)
            
            # لصق الشعار
            qr_img.paste(logo, pos)
            
            return qr_img
            
        except Exception as e:
            print(f"خطأ في إضافة الشعار: {e}")
            return qr_img
    
    def verify_qr_code(self, scanned_qr: str) -> Optional[Dict[str, Any]]:
        """
        التحقق من صحة رمز QR المبسط
        :param scanned_qr: رمز QR المسحوب
        :return: بيانات الموظف إذا كان الرمز صحيحاً
        """
        try:
            # التحقق من التنسيق الجديد (مفصول بـ |)
            if '|' in scanned_qr:
                qr_parts = scanned_qr.split('|')
                qr_data = {}
                
                for part in qr_parts:
                    if ':' in part:
                        key, value = part.split(':', 1)
                        qr_data[key] = value
                
                # التحقق من وجود البيانات الأساسية
                if 'ID' not in qr_data:
                    return None
                
                employee_id = qr_data['ID']
                
                # التحقق من صحة employee_id
                if not employee_id.isdigit():
                    return None
                
                # التحقق من الطابع الزمني إذا كان موجوداً
                if 'TIME' in qr_data:
                    try:
                        # استخدام تنسيق التاريخ من الإعدادات
                        date_format = self.settings.get('date_format', '%Y%m%d%H%M%S')
                        qr_time = datetime.strptime(qr_data['TIME'], date_format)
                        current_time = datetime.now()
                        time_diff = current_time - qr_time
                        
                        # التحقق من فترة الصلاحية
                        expiry_days = self.settings.get('expiry_days', 30)
                        if time_diff.total_seconds() > expiry_days * 24 * 3600:
                            return None
                            
                    except ValueError:
                        # إذا فشل في تحليل التاريخ، تجاهل التحقق من الوقت
                        pass
                
                return {
                    'employee_id': employee_id,
                    'employee_code': qr_data.get('CODE', ''),
                    'timestamp': qr_data.get('TIME', ''),
                    'is_valid': True
                }
            
            # دعم التنسيق القديم للتوافق
            elif scanned_qr.startswith('EMP:'):
                parts = scanned_qr.split(':')
                if len(parts) != 4:
                    return None
                
                prefix, employee_id, employee_code, timestamp = parts
                
                # التحقق من صحة employee_id
                if not employee_id.isdigit():
                    return None
                
                # التحقق من أن الرمز حديث
                try:
                    # استخدام تنسيق التاريخ من الإعدادات
                    date_format = self.settings.get('date_format', '%Y%m%d%H%M%S')
                    qr_time = datetime.strptime(timestamp, date_format)
                    current_time = datetime.now()
                    time_diff = current_time - qr_time
                    
                    # التحقق من فترة الصلاحية
                    expiry_days = self.settings.get('expiry_days', 30)
                    if time_diff.total_seconds() > expiry_days * 24 * 3600:
                        return None
                        
                except ValueError:
                    return None
                
                return {
                    'employee_id': employee_id,
                    'employee_code': employee_code,
                    'timestamp': timestamp,
                    'is_valid': True
                }
            
            return None
            
        except Exception as e:
            print(f"خطأ في التحقق من رمز QR: {e}")
            return None
    
    def save_qr_image(self, qr_code: str, file_path: str, size: int = None) -> bool:
        """
        حفظ صورة QR Code إلى ملف
        :param qr_code: رمز QR
        :param file_path: مسار الملف
        :param size: حجم الصورة
        :return: True إذا تم الحفظ بنجاح
        """
        try:
            # استخدام الحجم من الإعدادات إذا لم يتم تحديده
            if size is None:
                size = self.settings.get('size', 300)
            
            # إنشاء رمز QR مع الإعدادات
            qr = qrcode.QRCode(
                version=1,
                error_correction=getattr(qrcode.constants, f'ERROR_CORRECT_{self.settings.get("error_correction", "L")}'),
                box_size=self.settings.get('box_size', 10),
                border=self.settings.get('border', 4)
            )
            
            # تحويل النص إلى UTF-8 bytes ثم إلى base64 لتجنب مشاكل التشفير
            try:
                safe_qr_code = base64.b64encode(qr_code.encode('utf-8')).decode('ascii')
                qr.add_data(safe_qr_code)
            except:
                # إذا فشل، استخدم النص الأصلي
                qr.add_data(qr_code)
            qr.make(fit=True)
            
            # إنشاء الصورة
            img = qr.make_image(
                fill_color=self.settings.get('foreground_color', '#000000'),
                back_color=self.settings.get('background_color', '#FFFFFF')
            )
            
            # إضافة شعار إذا كان مفعلاً
            if self.settings.get('add_logo') and self.settings.get('logo_path'):
                img = self.add_logo_to_qr(img, self.settings['logo_path'])
            
            # حفظ الصورة
            img.save(file_path, format='PNG', quality=self.settings.get('image_quality', 95))
            return True
            
        except Exception as e:
            print(f"Error saving QR image: {e}")
            return False
