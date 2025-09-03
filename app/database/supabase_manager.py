from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json
from ..core.supabase_config import supabase_config

class SupabaseManager:
    """
    A database manager that interfaces with Supabase for the attendance system.
    This provides a unified interface similar to the existing DatabaseManager.
    """
    
    def __init__(self):
        self.client = supabase_config.client
        
    def _execute_query(self, table: str, query: str, *args) -> List[Dict[str, Any]]:
        """Execute a raw SQL query on the specified table."""
        try:
            result = self.client.rpc('execute_query', {
                'query': query,
                'params': args
            }).execute()
            return result.data or []
        except Exception as e:
            print(f"Error executing query: {e}")
            return []
    
    # Employee Management
    def add_employee(self, employee_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add a new employee to the database."""
        try:
            result = self.client.table('employees').insert(employee_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error adding employee: {e}")
            # رفع الاستثناء للمعالجة في الطبقة العليا
            raise e
    
    def get_employee(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve an employee by ID."""
        try:
            result = self.client.table('employees').select('*').eq('id', employee_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting employee: {e}")
            return None
    
    # Attendance Management
    def record_attendance(self, attendance_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Record a new attendance entry."""
        try:
            result = self.client.table('attendance').insert(attendance_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error recording attendance: {e}")
            return None
    
    def get_employee_attendance(self, employee_id: int, start_date: str = None, end_date: str = None) -> List[Dict[str, Any]]:
        """Get attendance records for an employee within a date range."""
        try:
            query = self.client.table('attendance').select('*').eq('employee_id', employee_id)
            
            if start_date:
                query = query.gte('date', start_date)
            if end_date:
                query = query.lte('date', end_date)
                
            result = query.order('check_time', desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"Error getting attendance: {e}")
            return []
    
    # User Authentication
    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate a user with username and password."""
        try:
            # This is a simplified example. In production, use Supabase Auth
            result = self.client.table('users').select('*').eq('username', username).execute()
            if result.data:
                user = result.data[0]
                # Verify password (in production, use proper password hashing)
                if user.get('password') == password:  # In production, use proper password verification
                    return user
            return None
        except Exception as e:
            print(f"Authentication error: {e}")
            return None
    
    # Real-time Subscriptions
    def subscribe_to_attendance_updates(self, callback):
        """Subscribe to real-time attendance updates."""
        def handle_payload(payload):
            if payload['event_type'] in ['INSERT', 'UPDATE', 'DELETE']:
                callback(payload)
                
        return self.client.realtime.subscribe(
            'attendance',
            'postgres_changes',
            handle_payload,
            event='*',
            schema='public',
            table='attendance'
        )
    
    # 🆕 دوال إضافية للنظام الذكي
    def get_all_employees(self) -> List[Dict[str, Any]]:
        """الحصول على جميع الموظفين"""
        try:
            result = self.client.table('employees').select('*').execute()
            return result.data or []
        except Exception as e:
            print(f"Error getting all employees: {e}")
            return []
    
    def get_all_users(self) -> List[Dict[str, Any]]:
        """الحصول على جميع المستخدمين"""
        try:
            result = self.client.table('users').select('*').execute()
            return result.data or []
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
    
    def get_all_attendance(self) -> List[Dict[str, Any]]:
        """الحصول على جميع سجلات الحضور"""
        try:
            result = self.client.table('attendance').select('*').execute()
            return result.data or []
        except Exception as e:
            print(f"Error getting all attendance: {e}")
            return []
    
    def get_all_locations(self) -> List[Dict[str, Any]]:
        """الحصول على جميع المواقع"""
        try:
            result = self.client.table('locations').select('*').execute()
            return result.data or []
        except Exception as e:
            print(f"Error getting all locations: {e}")
            return []
    
    def get_all_holidays(self) -> List[Dict[str, Any]]:
        """الحصول على جميع الإجازات"""
        try:
            result = self.client.table('holidays').select('*').execute()
            return result.data or []
        except Exception as e:
            print(f"Error getting all holidays: {e}")
            return []
    
    def get_all_settings(self) -> Dict[str, Any]:
        """الحصول على جميع الإعدادات"""
        try:
            result = self.client.table('app_settings').select('*').execute()
            if result.data:
                # تحويل القائمة إلى قاموس
                settings = {}
                for item in result.data:
                    # استخدام key_name بدلاً من key
                    key = item.get('key_name', '') or item.get('key', '')
                    value = item.get('value', '')
                    if key:
                        settings[key] = value
                return settings
            return {}
        except Exception as e:
            print(f"Error getting all settings: {e}")
            return {}
    

    
    def add_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add a new user to the database."""
        try:
            result = self.client.table('users').insert(user_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error adding user: {e}")
            # رفع الاستثناء للمعالجة في الطبقة العليا
            raise e
    
    def update_employee(self, employee_id: str, employee_data: Dict[str, Any]) -> bool:
        """Update an employee."""
        try:
            result = self.client.table('employees').update(employee_data).eq('id', employee_id).execute()
            # Success إذا لم يكن هناك Error، حتى لو كانت البيانات فارغة
            return True
        except Exception as e:
            print(f"Error updating employee: {e}")
            # رفع الاستثناء للمعالجة في الطبقة العليا
            raise e
    
    def update_user(self, user_id: str, user_data: Dict[str, Any]) -> bool:
        """Update a user."""
        try:
            result = self.client.table('users').update(user_data).eq('id', user_id).execute()
            # Success إذا لم يكن هناك Error، حتى لو كانت البيانات فارغة
            return True
        except Exception as e:
            print(f"Error updating user: {e}")
            # رفع الاستثناء للمعالجة في الطبقة العليا
            raise e
    
    def update_attendance(self, attendance_id: str, attendance_data: Dict[str, Any]) -> bool:
        """Update an attendance record."""
        try:
            result = self.client.table('attendance').update(attendance_data).eq('id', attendance_id).execute()
            # Success إذا لم يكن هناك Error، حتى لو كانت البيانات فارغة
            return True
        except Exception as e:
            print(f"Error updating attendance: {e}")
            # رفع الاستثناء للمعالجة في الطبقة العليا
            raise e
    
    def delete_employee(self, employee_id: str) -> bool:
        """Delete an employee."""
        try:
            result = self.client.table('employees').delete().eq('id', employee_id).execute()
            # Supabase returns empty list on successful delete, check count instead
            return result.count is None or result.count >= 0
        except Exception as e:
            print(f"Error deleting employee: {e}")
            return False
    
    def delete_user(self, user_id: str) -> bool:
        """Delete a user."""
        try:
            result = self.client.table('users').delete().eq('id', user_id).execute()
            # Supabase returns empty list on successful delete, check count instead
            return result.count is None or result.count >= 0
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False
    
    def delete_attendance(self, attendance_id: str) -> bool:
        """Delete an attendance record."""
        try:
            result = self.client.table('attendance').delete().eq('id', attendance_id).execute()
            # Supabase returns empty list on successful delete, check count instead
            return result.count is None or result.count >= 0
        except Exception as e:
            print(f"Error deleting attendance: {e}")
            return False
    
    # Settings Management
    def update_setting(self, key: str, value: str) -> bool:
        """Update a setting in Supabase."""
        try:
            # محاولة upsert الإعداد في جدول app_settings (insert أو update)
            # تحديد المفتاح الفريد key_name
            result = self.client.table('app_settings').upsert({
                'key_name': key,
                'value': value
                # لا نحتاج لإضافة updated_at - سيتم تحديثه تلقائياً بواسطة Supabase
            }, on_conflict='key_name').execute()
            
            return True
        except Exception as e:
            print(f"Error upserting setting {key}: {e}")
            return False
    
    def get_setting(self, key: str) -> Optional[str]:
        """Get a setting from Supabase."""
        try:
            result = self.client.table('app_settings').select('value').eq('key_name', key).execute()
            return result.data[0]['value'] if result.data else None
        except Exception as e:
            print(f"Error getting setting {key}: {e}")
            return None

    # Location Management
    def add_location(self, location_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add a new location to the database."""
        try:
            result = self.client.table('locations').insert(location_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error adding location: {e}")
            raise e
    
    def update_location(self, location_id: str, location_data: Dict[str, Any]) -> bool:
        """Update a location."""
        try:
            result = self.client.table('locations').update(location_data).eq('id', location_id).execute()
            return True
        except Exception as e:
            print(f"Error updating location: {e}")
            raise e
    
    def delete_location(self, location_id: str) -> bool:
        """Delete a location."""
        try:
            result = self.client.table('locations').delete().eq('id', location_id).execute()
            return result.count is None or result.count >= 0
        except Exception as e:
            print(f"Error deleting location: {e}")
            return False
    
    def get_all_locations(self) -> List[Dict[str, Any]]:
        """Get all locations from Supabase."""
        try:
            result = self.client.table('locations').select('*').execute()
            return result.data or []
        except Exception as e:
            print(f"Error getting all locations: {e}")
            return []
    
    # Holiday Management
    def add_holiday(self, holiday_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add a new holiday to the database."""
        try:
            result = self.client.table('holidays').insert(holiday_data).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error adding holiday: {e}")
            raise e
    
    def update_holiday(self, holiday_id: str, holiday_data: Dict[str, Any]) -> bool:
        """Update a holiday."""
        try:
            result = self.client.table('holidays').update(holiday_data).eq('id', holiday_id).execute()
            return True
        except Exception as e:
            print(f"Error updating holiday: {e}")
            raise e
    
    def delete_holiday(self, holiday_id: str) -> bool:
        """Delete a holiday."""
        try:
            result = self.client.table('holidays').delete().eq('id', holiday_id).execute()
            return result.count is None or result.count >= 0
        except Exception as e:
            print(f"Error deleting holiday: {e}")
            return False
    
    def get_all_holidays(self) -> List[Dict[str, Any]]:
        """Get all holidays from Supabase."""
        try:
            result = self.client.table('holidays').select('*').execute()
            return result.data or []
        except Exception as e:
            print(f"Error getting all holidays: {e}")
            return []

# Singleton instance - سيتم إنشاؤه عند الحاجة فقط
_supabase_manager_instance = None

def get_supabase_manager():
    """Get or create a singleton instance of SupabaseManager."""
    global _supabase_manager_instance
    if _supabase_manager_instance is None:
        _supabase_manager_instance = SupabaseManager()
    return _supabase_manager_instance
