#!/usr/bin/env python3
"""
نظام التعرف على الوجه للأمان المتقدم
"""

import cv2
import numpy as np
import base64
import io
from PIL import Image
import face_recognition
import os
import json
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class FaceRecognitionSecurity:
    """نظام التعرف على الوجه للأمان المتقدم"""
    
    def __init__(self):
        self.face_encodings_db = {}
        self.load_face_database()
    
    def load_face_database(self):
        """تحميل قاعدة بيانات الوجوه"""
        try:
            db_path = "face_encodings.json"
            if os.path.exists(db_path):
                with open(db_path, 'r') as f:
                    self.face_encodings_db = json.load(f)
                logger.info(f"✅ تم تحميل {len(self.face_encodings_db)} وجه من قاعدة البيانات")
            else:
                logger.info("📝 إنشاء قاعدة بيانات وجوه جديدة")
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل قاعدة بيانات الوجوه: {e}")
            self.face_encodings_db = {}
    
    def save_face_database(self):
        """حفظ قاعدة بيانات الوجوه"""
        try:
            db_path = "face_encodings.json"
            with open(db_path, 'w') as f:
                json.dump(self.face_encodings_db, f)
            logger.info("✅ تم حفظ قاعدة بيانات الوجوه")
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ قاعدة بيانات الوجوه: {e}")
    
    def encode_face_from_image(self, image_data: str) -> Optional[List[float]]:
        """تشفير الوجه من صورة"""
        try:
            # تحويل base64 إلى صورة
            image_bytes = base64.b64decode(image_data)
            image = Image.open(io.BytesIO(image_bytes))
            image_rgb = image.convert('RGB')
            
            # تحويل إلى numpy array
            image_array = np.array(image_rgb)
            
            # البحث عن الوجوه
            face_locations = face_recognition.face_locations(image_array)
            
            if not face_locations:
                logger.warning("⚠️ لم يتم العثور على وجه في الصورة")
                return None
            
            # تشفير الوجه الأول
            face_encodings = face_recognition.face_encodings(image_array, face_locations)
            
            if face_encodings:
                return face_encodings[0].tolist()
            
            return None
            
        except Exception as e:
            logger.error(f"❌ خطأ في تشفير الوجه: {e}")
            return None
    
    def register_employee_face(self, employee_id: int, image_data: str) -> bool:
        """تسجيل وجه الموظف"""
        try:
            face_encoding = self.encode_face_from_image(image_data)
            
            if face_encoding is None:
                return False
            
            # حفظ التشفير
            self.face_encodings_db[str(employee_id)] = face_encoding
            self.save_face_database()
            
            logger.info(f"✅ تم تسجيل وجه الموظف {employee_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل وجه الموظف: {e}")
            return False
    
    def verify_employee_face(self, employee_id: int, image_data: str, tolerance: float = 0.6) -> bool:
        """التحقق من وجه الموظف"""
        try:
            # الحصول على التشفير المسجل
            if str(employee_id) not in self.face_encodings_db:
                logger.warning(f"⚠️ لا يوجد وجه مسجل للموظف {employee_id}")
                return False
            
            registered_encoding = np.array(self.face_encodings_db[str(employee_id)])
            
            # تشفير الوجه الحالي
            current_encoding = self.encode_face_from_image(image_data)
            
            if current_encoding is None:
                return False
            
            # مقارنة الوجوه
            face_distance = face_recognition.face_distance([registered_encoding], current_encoding)[0]
            
            is_match = face_distance <= tolerance
            
            if is_match:
                logger.info(f"✅ تم التحقق من وجه الموظف {employee_id} بنجاح")
            else:
                logger.warning(f"❌ فشل التحقق من وجه الموظف {employee_id}")
            
            return is_match
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من الوجه: {e}")
            return False
    
    def get_face_verification_status(self, employee_id: int) -> Dict:
        """الحصول على حالة التحقق من الوجه"""
        return {
            'has_registered_face': str(employee_id) in self.face_encodings_db,
            'face_verification_enabled': True,
            'employee_id': employee_id
        }
    
    def delete_employee_face(self, employee_id: int) -> bool:
        """حذف وجه الموظف"""
        try:
            if str(employee_id) in self.face_encodings_db:
                del self.face_encodings_db[str(employee_id)]
                self.save_face_database()
                logger.info(f"✅ تم حذف وجه الموظف {employee_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ خطأ في حذف وجه الموظف: {e}")
            return False

# إنشاء مثيل عام
face_security = FaceRecognitionSecurity()
