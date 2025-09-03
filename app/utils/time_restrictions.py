#!/usr/bin/env python3
"""
نظام القيود الزمنية المتقدم للأمان
"""

import json
import os
from datetime import datetime, time as dt_time, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class TimeRestrictionsManager:
    """مدير القيود الزمنية المتقدم"""
    
    def __init__(self):
        self.restrictions_db_path = "time_restrictions.json"
        self.restrictions_data = self.load_restrictions_data()
        
    def load_restrictions_data(self) -> Dict:
        """تحميل بيانات القيود الزمنية"""
        try:
            if os.path.exists(self.restrictions_db_path):
                with open(self.restrictions_db_path, 'r') as f:
                    return json.load(f)
            return {
                'global_restrictions': {
                    'enabled': True,
                    'work_hours': {
                        'start': '08:00',
                        'end': '17:00'
                    },
                    'allowed_days': [0, 1, 2, 3, 4],  # الاثنين إلى الجمعة
                    'break_times': [
                        {'start': '12:00', 'end': '13:00', 'description': 'Lunch Break'}
                    ],
                    'max_check_in_interval': 30,  # دقيقة
                    'min_work_duration': 60,  # دقيقة
                    'max_work_duration': 600  # دقيقة (10 ساعات)
                },
                'employee_restrictions': {},
                'department_restrictions': {},
                'holiday_restrictions': {
                    'enabled': True,
                    'allow_emergency_checkin': False
                }
            }
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل القيود الزمنية: {e}")
            return {}
    
    def save_restrictions_data(self):
        """حفظ بيانات القيود الزمنية"""
        try:
            with open(self.restrictions_db_path, 'w') as f:
                json.dump(self.restrictions_data, f, indent=2)
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ القيود الزمنية: {e}")
    
    def is_checkin_allowed(self, employee_id: int, check_time: datetime = None) -> Dict:
        """التحقق من السماح بتسجيل الحضور"""
        try:
            if check_time is None:
                check_time = datetime.now()
            
            # التحقق من القيود العامة
            global_check = self.check_global_restrictions(check_time)
            if not global_check['allowed']:
                return global_check
            
            # التحقق من قيود الموظف
            employee_check = self.check_employee_restrictions(employee_id, check_time)
            if not employee_check['allowed']:
                return employee_check
            
            # التحقق من قيود القسم
            department_check = self.check_department_restrictions(employee_id, check_time)
            if not department_check['allowed']:
                return department_check
            
            # التحقق من الإجازات
            holiday_check = self.check_holiday_restrictions(check_time)
            if not holiday_check['allowed']:
                return holiday_check
            
            return {
                'allowed': True,
                'message': 'Check-in allowed',
                'restrictions_checked': ['global', 'employee', 'department', 'holiday']
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من القيود الزمنية: {e}")
            return {
                'allowed': False,
                'error': 'Time restriction check failed',
                'message': 'Unable to verify time restrictions'
            }
    
    def check_global_restrictions(self, check_time: datetime) -> Dict:
        """التحقق من القيود العامة"""
        try:
            global_restrictions = self.restrictions_data.get('global_restrictions', {})
            
            if not global_restrictions.get('enabled', True):
                return {'allowed': True, 'message': 'Global restrictions disabled'}
            
            # التحقق من أيام العمل
            weekday = check_time.weekday()
            allowed_days = global_restrictions.get('allowed_days', [0, 1, 2, 3, 4])
            
            if weekday not in allowed_days:
                return {
                    'allowed': False,
                    'message': f'Check-in not allowed on {check_time.strftime("%A")}',
                    'restriction_type': 'day_of_week'
                }
            
            # التحقق من ساعات العمل
            work_hours = global_restrictions.get('work_hours', {})
            start_time = dt_time.fromisoformat(work_hours.get('start', '08:00'))
            end_time = dt_time.fromisoformat(work_hours.get('end', '17:00'))
            current_time = check_time.time()
            
            if not (start_time <= current_time <= end_time):
                return {
                    'allowed': False,
                    'message': f'Check-in only allowed between {start_time} and {end_time}',
                    'restriction_type': 'work_hours'
                }
            
            # التحقق من أوقات الراحة
            break_times = global_restrictions.get('break_times', [])
            for break_time in break_times:
                break_start = dt_time.fromisoformat(break_time['start'])
                break_end = dt_time.fromisoformat(break_time['end'])
                
                if break_start <= current_time <= break_end:
                    return {
                        'allowed': False,
                        'message': f'Check-in not allowed during {break_time.get("description", "break time")}',
                        'restriction_type': 'break_time'
                    }
            
            return {'allowed': True, 'message': 'Global restrictions passed'}
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من القيود العامة: {e}")
            return {'allowed': False, 'error': 'Global restriction check failed'}
    
    def check_employee_restrictions(self, employee_id: int, check_time: datetime) -> Dict:
        """التحقق من قيود الموظف"""
        try:
            employee_restrictions = self.restrictions_data.get('employee_restrictions', {}).get(str(employee_id), {})
            
            if not employee_restrictions:
                return {'allowed': True, 'message': 'No employee-specific restrictions'}
            
            # التحقق من القيود المخصصة للموظف
            if employee_restrictions.get('disabled', False):
                return {
                    'allowed': False,
                    'message': 'Employee check-in is disabled',
                    'restriction_type': 'employee_disabled'
                }
            
            # التحقق من ساعات العمل المخصصة
            custom_hours = employee_restrictions.get('work_hours')
            if custom_hours:
                start_time = dt_time.fromisoformat(custom_hours.get('start', '08:00'))
                end_time = dt_time.fromisoformat(custom_hours.get('end', '17:00'))
                current_time = check_time.time()
                
                if not (start_time <= current_time <= end_time):
                    return {
                        'allowed': False,
                        'message': f'Employee check-in only allowed between {start_time} and {end_time}',
                        'restriction_type': 'employee_work_hours'
                    }
            
            return {'allowed': True, 'message': 'Employee restrictions passed'}
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من قيود الموظف: {e}")
            return {'allowed': False, 'error': 'Employee restriction check failed'}
    
    def check_department_restrictions(self, employee_id: int, check_time: datetime) -> Dict:
        """التحقق من قيود القسم"""
        try:
            # الحصول على قسم الموظف (يجب تنفيذ هذا من قاعدة البيانات)
            # department = get_employee_department(employee_id)
            
            # للآن، سنستخدم قسم افتراضي
            department = 'default'
            
            department_restrictions = self.restrictions_data.get('department_restrictions', {}).get(department, {})
            
            if not department_restrictions:
                return {'allowed': True, 'message': 'No department-specific restrictions'}
            
            # التحقق من قيود القسم
            if department_restrictions.get('disabled', False):
                return {
                    'allowed': False,
                    'message': f'Check-in disabled for {department} department',
                    'restriction_type': 'department_disabled'
                }
            
            return {'allowed': True, 'message': 'Department restrictions passed'}
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من قيود القسم: {e}")
            return {'allowed': False, 'error': 'Department restriction check failed'}
    
    def check_holiday_restrictions(self, check_time: datetime) -> Dict:
        """التحقق من قيود الإجازات"""
        try:
            holiday_restrictions = self.restrictions_data.get('holiday_restrictions', {})
            
            if not holiday_restrictions.get('enabled', True):
                return {'allowed': True, 'message': 'Holiday restrictions disabled'}
            
            # التحقق من الإجازات (يجب تنفيذ هذا من قاعدة البيانات)
            # is_holiday = is_date_holiday(check_time.date())
            
            # للآن، سنعتبر أن كل التواريخ عادية
            is_holiday = False
            
            if is_holiday:
                if not holiday_restrictions.get('allow_emergency_checkin', False):
                    return {
                        'allowed': False,
                        'message': 'Check-in not allowed on holidays',
                        'restriction_type': 'holiday'
                    }
                else:
                    return {
                        'allowed': True,
                        'message': 'Emergency check-in allowed on holiday',
                        'restriction_type': 'emergency_holiday'
                    }
            
            return {'allowed': True, 'message': 'Holiday restrictions passed'}
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من قيود الإجازات: {e}")
            return {'allowed': False, 'error': 'Holiday restriction check failed'}
    
    def set_employee_restrictions(self, employee_id: int, restrictions: Dict) -> bool:
        """تعيين قيود للموظف"""
        try:
            if 'employee_restrictions' not in self.restrictions_data:
                self.restrictions_data['employee_restrictions'] = {}
            
            self.restrictions_data['employee_restrictions'][str(employee_id)] = restrictions
            self.save_restrictions_data()
            
            logger.info(f"✅ تم تعيين قيود للموظف {employee_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تعيين قيود الموظف: {e}")
            return False
    
    def get_employee_restrictions(self, employee_id: int) -> Dict:
        """الحصول على قيود الموظف"""
        try:
            return self.restrictions_data.get('employee_restrictions', {}).get(str(employee_id), {})
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على قيود الموظف: {e}")
            return {}
    
    def update_global_restrictions(self, restrictions: Dict) -> bool:
        """تحديث القيود العامة"""
        try:
            self.restrictions_data['global_restrictions'].update(restrictions)
            self.save_restrictions_data()
            
            logger.info("✅ تم تحديث القيود العامة")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحديث القيود العامة: {e}")
            return False

# إنشاء مثيل عام
time_restrictions = TimeRestrictionsManager()
