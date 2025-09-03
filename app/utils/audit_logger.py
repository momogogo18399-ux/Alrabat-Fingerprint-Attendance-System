#!/usr/bin/env python3
"""
نظام سجل التدقيق الشامل للأمان
"""

import json
import os
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging
import threading

logger = logging.getLogger(__name__)

class AuditLogger:
    """نظام سجل التدقيق الشامل"""
    
    def __init__(self):
        self.audit_db_path = "audit_log.json"
        self.audit_data = self.load_audit_data()
        self.lock = threading.Lock()
        
        # إعدادات التدقيق
        self.max_log_entries = 10000
        self.log_retention_days = 365
        
    def load_audit_data(self) -> Dict:
        """تحميل بيانات التدقيق"""
        try:
            if os.path.exists(self.audit_db_path):
                with open(self.audit_db_path, 'r') as f:
                    return json.load(f)
            return {
                'audit_entries': [],
                'security_events': [],
                'access_logs': [],
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'last_cleanup': None,
                    'total_entries': 0
                }
            }
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل سجل التدقيق: {e}")
            return {
                'audit_entries': [],
                'security_events': [],
                'access_logs': [],
                'metadata': {
                    'created_at': datetime.now().isoformat(),
                    'last_cleanup': None,
                    'total_entries': 0
                }
            }
    
    def save_audit_data(self):
        """حفظ بيانات التدقيق"""
        try:
            with self.lock:
                with open(self.audit_db_path, 'w') as f:
                    json.dump(self.audit_data, f, indent=2)
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ سجل التدقيق: {e}")
    
    def log_attendance_event(self, employee_id: int, event_type: str, 
                           details: Dict, ip_address: str = None, 
                           user_agent: str = None) -> str:
        """تسجيل حدث الحضور"""
        try:
            event_id = self.generate_event_id()
            
            audit_entry = {
                'event_id': event_id,
                'timestamp': datetime.now().isoformat(),
                'event_type': 'attendance',
                'sub_type': event_type,
                'employee_id': employee_id,
                'details': details,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'severity': self.get_event_severity(event_type),
                'hash': self.calculate_event_hash(employee_id, event_type, details)
            }
            
            with self.lock:
                self.audit_data['audit_entries'].append(audit_entry)
                self.audit_data['metadata']['total_entries'] += 1
                
                # تنظيف السجل إذا تجاوز الحد الأقصى
                if len(self.audit_data['audit_entries']) > self.max_log_entries:
                    self.audit_data['audit_entries'] = self.audit_data['audit_entries'][-self.max_log_entries:]
            
            self.save_audit_data()
            
            logger.info(f"📝 تم تسجيل حدث الحضور: {event_type} للموظف {employee_id}")
            return event_id
            
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل حدث الحضور: {e}")
            return ""
    
    def log_security_event(self, event_type: str, details: Dict, 
                          employee_id: int = None, ip_address: str = None) -> str:
        """تسجيل حدث أمني"""
        try:
            event_id = self.generate_event_id()
            
            security_event = {
                'event_id': event_id,
                'timestamp': datetime.now().isoformat(),
                'event_type': 'security',
                'sub_type': event_type,
                'employee_id': employee_id,
                'details': details,
                'ip_address': ip_address,
                'severity': self.get_security_severity(event_type),
                'hash': self.calculate_event_hash(employee_id, event_type, details)
            }
            
            with self.lock:
                self.audit_data['security_events'].append(security_event)
            
            self.save_audit_data()
            
            logger.warning(f"🔒 تم تسجيل حدث أمني: {event_type}")
            return event_id
            
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل الحدث الأمني: {e}")
            return ""
    
    def log_access_event(self, user_id: int, action: str, resource: str, 
                        success: bool, ip_address: str = None) -> str:
        """تسجيل حدث الوصول"""
        try:
            event_id = self.generate_event_id()
            
            access_event = {
                'event_id': event_id,
                'timestamp': datetime.now().isoformat(),
                'event_type': 'access',
                'user_id': user_id,
                'action': action,
                'resource': resource,
                'success': success,
                'ip_address': ip_address,
                'severity': 'high' if not success else 'low'
            }
            
            with self.lock:
                self.audit_data['access_logs'].append(access_event)
            
            self.save_audit_data()
            
            logger.info(f"🔐 تم تسجيل حدث الوصول: {action} - {'نجح' if success else 'فشل'}")
            return event_id
            
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل حدث الوصول: {e}")
            return ""
    
    def log_biometric_verification(self, employee_id: int, verification_type: str, 
                                 success: bool, details: Dict) -> str:
        """تسجيل التحقق البيومتري"""
        try:
            event_type = f"biometric_{verification_type}_{'success' if success else 'failure'}"
            
            return self.log_security_event(
                event_type=event_type,
                details={
                    'employee_id': employee_id,
                    'verification_type': verification_type,
                    'success': success,
                    **details
                },
                employee_id=employee_id
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل التحقق البيومتري: {e}")
            return ""
    
    def log_face_recognition(self, employee_id: int, success: bool, 
                           confidence: float = None, details: Dict = None) -> str:
        """تسجيل التعرف على الوجه"""
        try:
            return self.log_biometric_verification(
                employee_id=employee_id,
                verification_type='face_recognition',
                success=success,
                details={
                    'confidence': confidence,
                    **(details or {})
                }
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل التعرف على الوجه: {e}")
            return ""
    
    def log_device_verification(self, employee_id: int, device_fingerprint: str, 
                              device_token: str, success: bool) -> str:
        """تسجيل التحقق من الجهاز"""
        try:
            return self.log_security_event(
                event_type=f"device_verification_{'success' if success else 'failure'}",
                details={
                    'employee_id': employee_id,
                    'device_fingerprint': device_fingerprint[:8] + '...',  # إخفاء جزء من البصمة
                    'device_token': device_token[:8] + '...',  # إخفاء جزء من التوكن
                    'success': success
                },
                employee_id=employee_id
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل التحقق من الجهاز: {e}")
            return ""
    
    def log_time_restriction_violation(self, employee_id: int, restriction_type: str, 
                                     details: Dict) -> str:
        """تسجيل انتهاك القيود الزمنية"""
        try:
            return self.log_security_event(
                event_type='time_restriction_violation',
                details={
                    'employee_id': employee_id,
                    'restriction_type': restriction_type,
                    **details
                },
                employee_id=employee_id
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل انتهاك القيود الزمنية: {e}")
            return ""
    
    def generate_event_id(self) -> str:
        """إنشاء معرف فريد للحدث"""
        try:
            timestamp = datetime.now().isoformat()
            random_part = hashlib.md5(timestamp.encode()).hexdigest()[:8]
            return f"EVT_{timestamp.replace(':', '').replace('-', '').replace('.', '')}_{random_part}"
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء معرف الحدث: {e}")
            return f"EVT_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    def calculate_event_hash(self, employee_id: int, event_type: str, details: Dict) -> str:
        """حساب hash للحدث"""
        try:
            data_string = f"{employee_id}_{event_type}_{json.dumps(details, sort_keys=True)}"
            return hashlib.sha256(data_string.encode()).hexdigest()[:16]
        except Exception as e:
            logger.error(f"❌ خطأ في حساب hash الحدث: {e}")
            return ""
    
    def get_event_severity(self, event_type: str) -> str:
        """تحديد مستوى خطورة الحدث"""
        high_severity_events = [
            'checkin_fraud_attempt',
            'device_spoofing',
            'unauthorized_access',
            'multiple_failed_attempts'
        ]
        
        medium_severity_events = [
            'checkin_outside_hours',
            'device_mismatch',
            'location_violation'
        ]
        
        if event_type in high_severity_events:
            return 'high'
        elif event_type in medium_severity_events:
            return 'medium'
        else:
            return 'low'
    
    def get_security_severity(self, event_type: str) -> str:
        """تحديد مستوى خطورة الحدث الأمني"""
        if 'failure' in event_type or 'violation' in event_type:
            return 'high'
        elif 'attempt' in event_type:
            return 'medium'
        else:
            return 'low'
    
    def get_audit_report(self, start_date: str = None, end_date: str = None, 
                        event_type: str = None, employee_id: int = None) -> Dict:
        """الحصول على تقرير التدقيق"""
        try:
            with self.lock:
                all_events = []
                all_events.extend(self.audit_data['audit_entries'])
                all_events.extend(self.audit_data['security_events'])
                all_events.extend(self.audit_data['access_logs'])
                
                # فلترة الأحداث
                filtered_events = []
                for event in all_events:
                    # فلترة حسب التاريخ
                    if start_date and event['timestamp'] < start_date:
                        continue
                    if end_date and event['timestamp'] > end_date:
                        continue
                    
                    # فلترة حسب نوع الحدث
                    if event_type and event.get('event_type') != event_type:
                        continue
                    
                    # فلترة حسب الموظف
                    if employee_id and event.get('employee_id') != employee_id:
                        continue
                    
                    filtered_events.append(event)
                
                # ترتيب حسب التاريخ
                filtered_events.sort(key=lambda x: x['timestamp'], reverse=True)
                
                return {
                    'total_events': len(filtered_events),
                    'events': filtered_events[:1000],  # آخر 1000 حدث
                    'summary': self.generate_audit_summary(filtered_events)
                }
                
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء تقرير التدقيق: {e}")
            return {'total_events': 0, 'events': [], 'summary': {}}
    
    def generate_audit_summary(self, events: List[Dict]) -> Dict:
        """إنشاء ملخص التدقيق"""
        try:
            summary = {
                'total_events': len(events),
                'by_type': {},
                'by_severity': {'high': 0, 'medium': 0, 'low': 0},
                'by_employee': {},
                'recent_activity': []
            }
            
            for event in events:
                # حسب النوع
                event_type = event.get('event_type', 'unknown')
                summary['by_type'][event_type] = summary['by_type'].get(event_type, 0) + 1
                
                # حسب الخطورة
                severity = event.get('severity', 'low')
                summary['by_severity'][severity] += 1
                
                # حسب الموظف
                emp_id = event.get('employee_id')
                if emp_id:
                    summary['by_employee'][emp_id] = summary['by_employee'].get(emp_id, 0) + 1
            
            # آخر 10 أحداث
            summary['recent_activity'] = events[:10]
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء ملخص التدقيق: {e}")
            return {}

# إنشاء مثيل عام
audit_logger = AuditLogger()
