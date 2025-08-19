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
            return None
    
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

# Create a singleton instance
supabase_manager = SupabaseManager()
