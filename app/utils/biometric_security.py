#!/usr/bin/env python3
"""
نظام التحقق البيومتري المتقدم للأمان
"""

import hashlib
import time
import json
import os
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import random
import string

logger = logging.getLogger(__name__)

class BiometricSecurityManager:
    """مدير الأمان البيومتري المتقدم"""
    
    def __init__(self):
        self.security_db_path = "biometric_security.json"
        self.security_data = self.load_security_data()
        
        # إعدادات الأمان
        self.max_failed_attempts = 3
        self.lockout_duration = 300  # 5 دقائق
        self.verification_timeout = 30  # 30 ثانية
        
    def load_security_data(self) -> Dict:
        """تحميل بيانات الأمان"""
        try:
            if os.path.exists(self.security_db_path):
                with open(self.security_db_path, 'r') as f:
                    return json.load(f)
            return {
                'failed_attempts': {},
                'lockouts': {},
                'verification_sessions': {},
                'security_events': []
            }
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل بيانات الأمان: {e}")
            return {
                'failed_attempts': {},
                'lockouts': {},
                'verification_sessions': {},
                'security_events': []
            }
    
    def save_security_data(self):
        """حفظ بيانات الأمان"""
        try:
            with open(self.security_db_path, 'w') as f:
                json.dump(self.security_data, f, indent=2)
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ بيانات الأمان: {e}")
    
    def generate_verification_challenge(self, employee_id: int) -> Dict:
        """إنشاء تحدي التحقق"""
        try:
            # إنشاء تحدي عشوائي
            challenge = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            timestamp = time.time()
            
            # حفظ جلسة التحقق
            session_id = f"{employee_id}_{timestamp}"
            self.security_data['verification_sessions'][session_id] = {
                'employee_id': employee_id,
                'challenge': challenge,
                'timestamp': timestamp,
                'expires_at': timestamp + self.verification_timeout,
                'used': False
            }
            
            self.save_security_data()
            
            logger.info(f"✅ تم إنشاء تحدي التحقق للموظف {employee_id}")
            
            return {
                'session_id': session_id,
                'challenge': challenge,
                'expires_in': self.verification_timeout
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء تحدي التحقق: {e}")
            return {}
    
    def verify_biometric_response(self, session_id: str, response: str, 
                                device_fingerprint: str, device_token: str) -> Dict:
        """التحقق من الاستجابة البيومترية"""
        try:
            # التحقق من صحة الجلسة
            if session_id not in self.security_data['verification_sessions']:
                return {'success': False, 'error': 'Invalid session'}
            
            session = self.security_data['verification_sessions'][session_id]
            
            # التحقق من انتهاء صلاحية الجلسة
            if time.time() > session['expires_at']:
                del self.security_data['verification_sessions'][session_id]
                self.save_security_data()
                return {'success': False, 'error': 'Session expired'}
            
            # التحقق من استخدام الجلسة
            if session['used']:
                return {'success': False, 'error': 'Session already used'}
            
            employee_id = session['employee_id']
            
            # التحقق من الحظر
            if self.is_employee_locked_out(employee_id):
                return {'success': False, 'error': 'Employee locked out'}
            
            # التحقق من الاستجابة
            expected_response = self.calculate_expected_response(
                session['challenge'], device_fingerprint, device_token
            )
            
            if response == expected_response:
                # نجح التحقق
                session['used'] = True
                self.clear_failed_attempts(employee_id)
                self.log_security_event(employee_id, 'biometric_verification_success')
                
                logger.info(f"✅ نجح التحقق البيومتري للموظف {employee_id}")
                
                return {
                    'success': True,
                    'message': 'Biometric verification successful',
                    'employee_id': employee_id
                }
            else:
                # فشل التحقق
                self.record_failed_attempt(employee_id)
                self.log_security_event(employee_id, 'biometric_verification_failed')
                
                logger.warning(f"❌ فشل التحقق البيومتري للموظف {employee_id}")
                
                return {
                    'success': False,
                    'error': 'Invalid biometric response',
                    'attempts_remaining': self.get_remaining_attempts(employee_id)
                }
                
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق البيومتري: {e}")
            return {'success': False, 'error': 'Verification error'}
    
    def calculate_expected_response(self, challenge: str, device_fingerprint: str, 
                                  device_token: str) -> str:
        """حساب الاستجابة المتوقعة"""
        try:
            # دمج البيانات
            combined_data = f"{challenge}_{device_fingerprint}_{device_token}"
            
            # إنشاء hash
            hash_object = hashlib.sha256(combined_data.encode())
            return hash_object.hexdigest()[:16]  # أول 16 حرف
            
        except Exception as e:
            logger.error(f"❌ خطأ في حساب الاستجابة: {e}")
            return ""
    
    def record_failed_attempt(self, employee_id: int):
        """تسجيل محاولة فاشلة"""
        try:
            if str(employee_id) not in self.security_data['failed_attempts']:
                self.security_data['failed_attempts'][str(employee_id)] = {
                    'count': 0,
                    'last_attempt': None
                }
            
            self.security_data['failed_attempts'][str(employee_id)]['count'] += 1
            self.security_data['failed_attempts'][str(employee_id)]['last_attempt'] = time.time()
            
            # التحقق من الحاجة للحظر
            if self.security_data['failed_attempts'][str(employee_id)]['count'] >= self.max_failed_attempts:
                self.lockout_employee(employee_id)
            
            self.save_security_data()
            
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل المحاولة الفاشلة: {e}")
    
    def clear_failed_attempts(self, employee_id: int):
        """مسح المحاولات الفاشلة"""
        try:
            if str(employee_id) in self.security_data['failed_attempts']:
                del self.security_data['failed_attempts'][str(employee_id)]
            if str(employee_id) in self.security_data['lockouts']:
                del self.security_data['lockouts'][str(employee_id)]
            self.save_security_data()
        except Exception as e:
            logger.error(f"❌ خطأ في مسح المحاولات الفاشلة: {e}")
    
    def lockout_employee(self, employee_id: int):
        """حظر الموظف مؤقتاً"""
        try:
            self.security_data['lockouts'][str(employee_id)] = {
                'locked_at': time.time(),
                'expires_at': time.time() + self.lockout_duration
            }
            self.save_security_data()
            
            logger.warning(f"🔒 تم حظر الموظف {employee_id} مؤقتاً")
            
        except Exception as e:
            logger.error(f"❌ خطأ في حظر الموظف: {e}")
    
    def is_employee_locked_out(self, employee_id: int) -> bool:
        """التحقق من حظر الموظف"""
        try:
            if str(employee_id) not in self.security_data['lockouts']:
                return False
            
            lockout = self.security_data['lockouts'][str(employee_id)]
            
            # التحقق من انتهاء الحظر
            if time.time() > lockout['expires_at']:
                del self.security_data['lockouts'][str(employee_id)]
                self.save_security_data()
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من الحظر: {e}")
            return False
    
    def get_remaining_attempts(self, employee_id: int) -> int:
        """الحصول على المحاولات المتبقية"""
        try:
            if str(employee_id) not in self.security_data['failed_attempts']:
                return self.max_failed_attempts
            
            failed_count = self.security_data['failed_attempts'][str(employee_id)]['count']
            return max(0, self.max_failed_attempts - failed_count)
            
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على المحاولات المتبقية: {e}")
            return 0
    
    def log_security_event(self, employee_id: int, event_type: str, details: str = ""):
        """تسجيل حدث أمني"""
        try:
            event = {
                'timestamp': datetime.now().isoformat(),
                'employee_id': employee_id,
                'event_type': event_type,
                'details': details,
                'ip_address': 'unknown'  # يمكن إضافة IP لاحقاً
            }
            
            self.security_data['security_events'].append(event)
            
            # الاحتفاظ بآخر 1000 حدث فقط
            if len(self.security_data['security_events']) > 1000:
                self.security_data['security_events'] = self.security_data['security_events'][-1000:]
            
            self.save_security_data()
            
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل الحدث الأمني: {e}")
    
    def get_security_status(self, employee_id: int) -> Dict:
        """الحصول على حالة الأمان للموظف"""
        try:
            return {
                'employee_id': employee_id,
                'is_locked_out': self.is_employee_locked_out(employee_id),
                'failed_attempts': self.security_data['failed_attempts'].get(str(employee_id), {}).get('count', 0),
                'remaining_attempts': self.get_remaining_attempts(employee_id),
                'last_failed_attempt': self.security_data['failed_attempts'].get(str(employee_id), {}).get('last_attempt'),
                'lockout_expires_at': self.security_data['lockouts'].get(str(employee_id), {}).get('expires_at')
            }
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على حالة الأمان: {e}")
            return {}

# إنشاء مثيل عام
biometric_security = BiometricSecurityManager()
