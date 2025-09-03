import os
import logging
import threading
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from .database_manager import DatabaseManager
from .supabase_manager import SupabaseManager

class HybridDatabaseManager:
    """
    مدير قاعدة البيانات الهجينة - نظام مبسط وفعال
    يعمل مع قاعدة البيانات المحلية أولاً ثم يزامن مع Supabase
    """
    
    def __init__(self, local_db_path: str, supabase_url: str = None, supabase_key: str = None):
        """
        تهيئة مدير قاعدة البيانات الهجينة
        """
        # تعيين متغير البيئة لمسار قاعدة البيانات المحلية
        os.environ['SQLITE_FILE'] = os.path.basename(local_db_path)
        
        # تهيئة قاعدة البيانات المحلية
        self.local_db = DatabaseManager()
        
        # إعداد التسجيل
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('HybridDB')
        
        # حالة المزامنة
        self.supabase_enabled = False
        self.supabase_manager = None
        
        # إعداد جدول التغييرات المعلقة
        self._setup_pending_changes_table()
        
        # مزامنة أولية مع سوبابيس
        if supabase_url and supabase_key:
            self._initial_supabase_sync(supabase_url, supabase_key)
        else:
            self.logger.info("🚫 No Supabase credentials - running in local-only mode")
    
    def _setup_pending_changes_table(self):
        """إعداد جدول التغييرات المعلقة"""
        try:
            self.local_db._execute_query_with_commit("""
                CREATE TABLE IF NOT EXISTS pending_changes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    record_id TEXT NOT NULL,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.logger.info("✅ Pending changes table setup complete")
        except Exception as e:
            self.logger.error(f"❌ Error setting up pending changes table: {e}")
    
    def _initial_supabase_sync(self, supabase_url: str, supabase_key: str):
        """مزامنة أولية مع سوبابيس"""
        try:
            self.logger.info("🔄 Initial connection to Supabase for data download...")
            
            # تهيئة مدير سوبابيس
            self.supabase_manager = SupabaseManager()
            
            # تحميل جميع البيانات من سوبابيس
            self._download_all_data_from_supabase()
            
            # تفعيل المزامنة
            self.supabase_enabled = True
            self.logger.info("✅ Initial Supabase sync completed successfully")
            self.logger.info("🔄 Supabase connection ENABLED - auto-sync active")
            
            # بدء المزامنة التلقائية
            self._start_auto_sync()
            
        except Exception as e:
            self.logger.error(f"❌ Error during initial Supabase sync: {e}")
            self.logger.warning("⚠️ Initial Supabase sync failed, but local database is ready")
    
    def _download_all_data_from_supabase(self):
        """تحميل جميع البيانات من سوبابيس"""
        try:
            # تحميل الموظفين
            self.logger.info("📥 Downloading employees from Supabase...")
            employees = self.supabase_manager.get_all_employees()
            new_employees = 0
            updated_employees = 0
            
            for emp in employees:
                try:
                    # التحقق من وجود الموظف
                    existing = self.local_db.get_employee_by_code(emp.get('employee_code'))
                    
                    if existing:
                        # Update الموظف الموجود
                        emp_data = {
                            'name': emp.get('name', 'Unknown'),
                            'job_title': emp.get('job_title', 'Unknown'),
                            'department': emp.get('department', 'Unknown'),
                            'phone_number': emp.get('phone_number', f"PHONE_{emp.get('id', 'UNK')}"),
                            'qr_code': emp.get('qr_code', ''),
                            'employee_code': emp.get('employee_code', f"EMP_{emp.get('id', 'XXX')}")
                        }
                        
                        if self.local_db.update_employee(existing['id'], emp_data):
                            updated_employees += 1
                        else:
                            self.logger.warning(f"⚠️ Failed to update employee: {emp.get('name', 'Unknown')}")
                    else:
                        # Add new employee
                        emp_data = {
                            'employee_code': emp.get('employee_code', f"EMP_{emp.get('id', 'XXX')}"),
                            'name': emp.get('name', 'Unknown'),
                            'job_title': emp.get('job_title', 'Unknown'),
                            'department': emp.get('department', 'Unknown'),
                            'phone_number': emp.get('phone_number', f"PHONE_{emp.get('id', 'UNK')}"),
                            'qr_code': emp.get('qr_code', '')
                        }
                        
                        if self.local_db.add_employee(emp_data):
                            new_employees += 1
                            self.logger.info(f"✅ Downloaded new employee: {emp.get('name', 'Unknown')}")
                        else:
                            self.logger.warning(f"⚠️ Failed to add employee: {emp.get('name', 'Unknown')}")
                            
                except Exception as e:
                    self.logger.warning(f"⚠️ Skipping employee {emp.get('name', 'Unknown')}: {e}")
            
            # تحميل المستخدمين
            self.logger.info("📥 Downloading users from Supabase...")
            users = self.supabase_manager.get_all_users()
            for user in users:
                try:
                    if not self.local_db.get_user_by_username(user.get('username')):
                        user_data = {
                            'username': user.get('username'),
                            'password': user.get('password', 'default123'),
                            'role': user.get('role', 'user')
                        }
                        if self.local_db.add_user(user_data):
                            self.logger.info(f"✅ Downloaded user: {user.get('username')}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to download user {user.get('username')}: {e}")
            
            # تحميل سجلات الحضور
            self.logger.info("📥 Downloading attendance records from Supabase...")
            attendance_records = self.supabase_manager.get_all_attendance()
            for record in attendance_records:
                try:
                    # الSearch عن الموظف
                    employee = self.local_db.get_employee_by_code(record.get('employee_code'))
                    if employee:
                        # إعداد بيانات الحضور
                        check_time = record.get('check_time') or record.get('check_in') or record.get('check_out') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        attendance_data = {
                            'employee_id': str(employee['id']),
                            'check_time': check_time,
                            'date': record.get('date', datetime.now().strftime('%Y-%m-%d')),
                            'type': record.get('type', 'Check-In'),
                            'notes': record.get('notes', '')
                        }
                        
                        if self.local_db.add_attendance_record(attendance_data):
                            self.logger.info(f"✅ Downloaded attendance record for: {employee.get('name')}")
                        else:
                            self.logger.warning(f"⚠️ Failed to download attendance record for: {employee.get('name')}")
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to download attendance record: {e}")
            
            self.logger.info(f"✅ Total: {new_employees} new employees, {updated_employees} updated employees, {len(users)} users, {len(attendance_records)} attendance records")
            
        except Exception as e:
            self.logger.error(f"❌ Error downloading data from Supabase: {e}")
            raise
    
    def _start_auto_sync(self):
        """بدء المزامنة التلقائية"""
        if not self.supabase_enabled:
            self.logger.info("🚫 Auto-sync disabled - Supabase is not available")
            return
        
        def auto_sync():
            self.logger.info("🔄 Auto-sync started - syncing every 5 seconds")
            while self.supabase_enabled:
                try:
                    time.sleep(5)  # مزامنة كل 5 ثواني
                    self._background_sync()
                except Exception as e:
                    self.logger.error(f"Auto-sync error: {e}")
        
        sync_thread = threading.Thread(target=auto_sync, daemon=True)
        sync_thread.start()
        self.logger.info("✅ Auto-sync thread started")
    
    def _background_sync(self):
        """مزامنة في الخلفية"""
        if not self.supabase_enabled:
            return
        
        try:
            self.logger.info("🔄 Background sync running...")
            self._sync_pending_changes()
            self.logger.info("✅ Background sync completed")
        except Exception as e:
            self.logger.error(f"Background sync error: {e}")
    
    def _sync_pending_changes(self):
        """مزامنة التغييرات المعلقة مع سوبابيس"""
        if not self.supabase_enabled:
            return
        
        try:
            # جلب التغييرات المعلقة
            changes = self.local_db._execute_query(
                "SELECT * FROM pending_changes ORDER BY created_at ASC",
                fetch=True
            )
            
            if not changes:
                self.logger.info("📝 No pending changes to sync")
                return
            
            self.logger.info(f"🔄 Syncing {len(changes)} pending changes...")
            
            for change in changes:
                try:
                    self.logger.info(f"📝 Syncing {change['operation']} for {change['table_name']}:{change['record_id']}")
                    
                    # تطبيق التغيير على سوبابيس
                    if change['operation'] == 'INSERT':
                        self._sync_insert(change)
                    elif change['operation'] == 'UPDATE':
                        self._sync_update(change)
                    elif change['operation'] == 'DELETE':
                        self._sync_delete(change)
                    
                    # Delete التغيير من الجدول
                    self.local_db._execute_query_with_commit(
                        "DELETE FROM pending_changes WHERE id = ?",
                        (change['id'],)
                    )
                    
                    self.logger.info(f"✅ Synced {change['operation']} for {change['table_name']}:{change['record_id']}")
                    
                except Exception as e:
                    self.logger.error(f"Error syncing change {change['id']}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error in pending changes sync: {e}")
    
    def _sync_insert(self, change):
        """مزامنة إدراج جديد"""
        if not self.supabase_enabled:
            return
        
        try:
            if change['table_name'] == 'employees':
                data = json.loads(change['data'])
                result = self.supabase_manager.add_employee(data)
                if result:
                    self.logger.info(f"✅ Added employee to Supabase: {data.get('name', 'Unknown')}")
                else:
                    self.logger.error(f"❌ Failed to add employee to Supabase: {data.get('name', 'Unknown')}")
            elif change['table_name'] == 'users':
                data = json.loads(change['data'])
                result = self.supabase_manager.add_user(data)
                if result:
                    self.logger.info(f"✅ Added user to Supabase: {data.get('username', 'Unknown')}")
                else:
                    self.logger.error(f"❌ Failed to add user to Supabase: {data.get('username', 'Unknown')}")
            elif change['table_name'] == 'attendance':
                data = json.loads(change['data'])
                result = self.supabase_manager.add_attendance(data)
                if result:
                    self.logger.info(f"✅ Added attendance to Supabase")
                else:
                    self.logger.error(f"❌ Failed to add attendance to Supabase")
        except Exception as e:
            self.logger.error(f"Error syncing insert: {e}")
    
    def _sync_update(self, change):
        """مزامنة Update"""
        if not self.supabase_enabled:
            return
        
        try:
            if change['table_name'] == 'employees':
                data = json.loads(change['data'])
                result = self.supabase_manager.update_employee(change['record_id'], data)
                if result:
                    self.logger.info(f"✅ Updated employee in Supabase: {change['record_id']}")
                else:
                    self.logger.error(f"❌ Failed to update employee in Supabase: {change['record_id']}")
            elif change['table_name'] == 'users':
                data = json.loads(change['data'])
                result = self.supabase_manager.update_user(change['record_id'], data)
                if result:
                    self.logger.info(f"✅ Updated user in Supabase: {change['record_id']}")
                else:
                    self.logger.error(f"❌ Failed to update user in Supabase: {change['record_id']}")
            elif change['table_name'] == 'attendance':
                data = json.loads(change['data'])
                result = self.supabase_manager.update_attendance(change['record_id'], data)
                if result:
                    self.logger.info(f"✅ Updated attendance in Supabase: {change['record_id']}")
                else:
                    self.logger.error(f"❌ Failed to update attendance in Supabase: {change['record_id']}")
        except Exception as e:
            self.logger.error(f"Error syncing update: {e}")
    
    def _sync_delete(self, change):
        """مزامنة Delete"""
        if not self.supabase_enabled:
            return
        
        try:
            if change['table_name'] == 'employees':
                result = self.supabase_manager.delete_employee(change['record_id'])
                if result:
                    self.logger.info(f"✅ Deleted employee from Supabase: {change['record_id']}")
                else:
                    self.logger.error(f"❌ Failed to delete employee from Supabase: {change['record_id']}")
            elif change['table_name'] == 'users':
                result = self.supabase_manager.delete_user(change['record_id'])
                if result:
                    self.logger.info(f"✅ Deleted user from Supabase: {change['record_id']}")
                else:
                    self.logger.error(f"❌ Failed to delete user from Supabase: {change['record_id']}")
            elif change['table_name'] == 'attendance':
                result = self.supabase_manager.delete_attendance(change['record_id'])
                if result:
                    self.logger.info(f"✅ Deleted attendance from Supabase: {change['record_id']}")
                else:
                    self.logger.error(f"❌ Failed to delete attendance from Supabase: {change['record_id']}")
        except Exception as e:
            self.logger.error(f"Error syncing delete: {e}")
    
    def _record_change(self, table_name: str, operation: str, record_id: str, data: Dict[str, Any] = None):
        """تسجيل تغيير للمزامنة المستقبلية"""
        if not self.supabase_enabled:
            self.logger.warning(f"🚫 Cannot record change - Supabase is not available")
            return
        
        try:
            data_json = json.dumps(data) if data else '{}'
            
            self.local_db._execute_query_with_commit(
                "INSERT INTO pending_changes (table_name, operation, record_id, data) VALUES (?, ?, ?, ?)",
                (table_name, operation, record_id, data_json)
            )
            self.logger.info(f"📝 Recorded {operation} change for {table_name}:{record_id}")
            
            # مزامنة فورية
            self._immediate_sync(table_name, operation, record_id, data)
            
        except Exception as e:
            self.logger.error(f"Error recording change: {e}")
    
    def _immediate_sync(self, table_name: str, operation: str, record_id: str, data: Dict[str, Any] = None):
        """مزامنة فورية مع Supabase"""
        if not self.supabase_enabled:
            return
        
        try:
            self.logger.info(f"⚡ Immediate sync: {operation} for {table_name}:{record_id}")
            
            if operation == 'INSERT':
                if table_name == 'employees':
                    result = self.supabase_manager.add_employee(data)
                    if result:
                        self.logger.info(f"✅ Immediately added employee to Supabase: {data.get('name', 'Unknown')}")
                    else:
                        self.logger.error(f"❌ Failed to immediately add employee to Supabase: {data.get('name', 'Unknown')}")
                elif table_name == 'users':
                    result = self.supabase_manager.add_user(data)
                    if result:
                        self.logger.info(f"✅ Immediately added user to Supabase: {data.get('username', 'Unknown')}")
                    else:
                        self.logger.error(f"❌ Failed to immediately add user to Supabase: {data.get('username', 'Unknown')}")
                elif table_name == 'attendance':
                    result = self.supabase_manager.add_attendance(data)
                    if result:
                        self.logger.info(f"✅ Immediately added attendance to Supabase")
                    else:
                        self.logger.error(f"❌ Failed to immediately add attendance to Supabase")
                        
            elif operation == 'UPDATE':
                if table_name == 'employees':
                    result = self.supabase_manager.update_employee(record_id, data)
                    if result:
                        self.logger.info(f"✅ Immediately updated employee in Supabase: {record_id}")
                    else:
                        self.logger.error(f"❌ Failed to immediately update employee in Supabase: {record_id}")
                        
            elif operation == 'DELETE':
                if table_name == 'employees':
                    result = self.supabase_manager.delete_employee(record_id)
                    if result:
                        self.logger.info(f"✅ Immediately deleted employee from Supabase: {record_id}")
                    else:
                        self.logger.error(f"❌ Failed to immediately delete employee from Supabase: {record_id}")
                elif table_name == 'users':
                    result = self.supabase_manager.delete_user(record_id)
                    if result:
                        self.logger.info(f"✅ Immediately deleted user from Supabase: {record_id}")
                    else:
                        self.logger.error(f"❌ Failed to immediately delete user from Supabase: {record_id}")
                elif table_name == 'attendance':
                    result = self.supabase_manager.delete_attendance(record_id)
                    if result:
                        self.logger.info(f"✅ Immediately deleted attendance from Supabase: {record_id}")
                    else:
                        self.logger.error(f"❌ Failed to immediately delete attendance from Supabase: {record_id}")
                        
        except Exception as e:
            self.logger.error(f"Error in immediate sync: {e}")
    
    # --- واجهة قاعدة البيانات المحلية ---
    
    def get_all_employees(self):
        """جلب جميع الموظفين من قاعدة البيانات المحلية"""
        return self.local_db.get_all_employees()
    
    def get_employee_by_id(self, employee_id):
        """جلب موظف بالمعرف من قاعدة البيانات المحلية"""
        return self.local_db.get_employee_by_id(employee_id)
    
    def get_employee_by_code(self, employee_code):
        """جلب موظف بالرمز من قاعدة البيانات المحلية"""
        return self.local_db.get_employee_by_code(employee_code)
    
    def get_employee_by_phone(self, phone_number):
        """جلب موظف برقم الهاتف من قاعدة البيانات المحلية"""
        return self.local_db.get_employee_by_phone(phone_number)
    
    def get_employee_by_token(self, token):
        """جلب موظف بالرمز المميز من قاعدة البيانات المحلية"""
        return self.local_db.get_employee_by_token(token)
    
    def get_employee_by_fingerprint(self, fingerprint):
        """جلب موظف بالبصمة من قاعدة البيانات المحلية"""
        return self.local_db.get_employee_by_fingerprint(fingerprint)
    
    def add_employee(self, data):
        """Add new employee إلى قاعدة البيانات المحلية"""
        result = self.local_db.add_employee(data)
        if result:
            self._record_change('employees', 'INSERT', str(result), data)
        return result
    
    def update_employee(self, employee_id, employee_data):
        """Update employee في قاعدة البيانات المحلية"""
        result = self.local_db.update_employee(employee_id, employee_data)
        if result:
            self._record_change('employees', 'UPDATE', str(employee_id), employee_data)
        return result
    
    def delete_employee(self, employee_id):
        """Delete موظف من قاعدة البيانات المحلية"""
        result = self.local_db.delete_employee(employee_id)
        if result:
            self._record_change('employees', 'DELETE', str(employee_id))
        return result
    
    def record_attendance(self, employee_id, attendance_type, location_id=None, notes=None):
        """تسجيل حضور في قاعدة البيانات المحلية"""
        result = self.local_db.record_attendance(employee_id, attendance_type, location_id, notes)
        if result:
            # تسجيل التغيير للمزامنة المستقبلية
            attendance_data = {
                'employee_id': employee_id,
                'type': attendance_type,
                'location_id': location_id,
                'notes': notes,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self._record_change('attendance', 'INSERT', str(result), attendance_data)
        return result
    
    def add_user(self, user_data):
        """Add مستخدم جديد إلى قاعدة البيانات المحلية"""
        result = self.local_db.add_user(user_data)
        if result:
            self._record_change('users', 'INSERT', str(result), user_data)
        return result
    
    def update_setting(self, key, value):
        """Update إعداد في قاعدة البيانات المحلية"""
        return self.local_db.update_setting(key, value)
    
    def get_all_settings(self):
        """جلب جميع الإعدادات من قاعدة البيانات المحلية"""
        return self.local_db.get_all_settings()
    
    def get_setting(self, key, default=None):
        """جلب إعداد من قاعدة البيانات المحلية"""
        return self.local_db.get_setting(key, default)
    
    def save_setting(self, key, value):
        """Save إعداد في قاعدة البيانات المحلية"""
        return self.local_db.save_setting(key, value)
    
    def sync_now(self):
        """مزامنة فورية"""
        if not self.supabase_enabled:
            self.logger.info("🚫 Supabase is disabled - no sync possible")
            return False
        
        try:
            self._background_sync()
            return True
        except Exception as e:
            self.logger.error(f"Sync error: {e}")
            return False
    
    def force_sync_with_web(self):
        """مزامنة إجبارية مع الويب"""
        if not self.supabase_enabled:
            self.logger.info("🚫 Supabase is disabled - no web sync possible")
            return False
        
        try:
            # مزامنة كاملة مع سوبابيس
            self._download_all_data_from_supabase()
            return True
        except Exception as e:
            self.logger.error(f"Force sync error: {e}")
            return False
    
    def get_sync_status(self):
        """الحصول على حالة المزامنة"""
        return {
            'supabase_enabled': self.supabase_enabled,
            'local_database': 'SQLite',
            'sync_mode': 'INSTANT + AUTO-SYNC (Supabase enabled for real-time sync)' if self.supabase_enabled else 'Local-only mode'
        }
    
    def get_web_sync_status(self):
        """الحصول على حالة مزامنة الويب"""
        return {
            'web_sync_enabled': self.supabase_enabled,
            'last_sync': 'Initial sync completed' if self.supabase_enabled else 'Never',
            'next_sync': 'Every 5 seconds' if self.supabase_enabled else 'Disabled',
            'pending_changes': 0 if not self.supabase_enabled else 'Unknown'
        }
    
    def cleanup_on_exit(self):
        """تنظيف عند الخروج"""
        try:
            if self.local_db:
                # مزامنة نهائية (محلية فقط)
                self.logger.info("🔄 Performing final local sync...")
                
                # Delete قاعدة البيانات المحلية (اختياري)
                if hasattr(self.local_db, 'database_file'):
                    import os
                    try:
                        os.remove(self.local_db.database_file)
                        self.logger.info("🗑️ Local database removed")
                    except:
                        pass
                
                self.local_db = None
                
        except Exception as e:
            self.logger.error(f"Cleanup error: {e}")
    
    def __getattr__(self, name):
        """تمرير الدوال غير المعرفة إلى قاعدة البيانات المحلية"""
        if hasattr(self.local_db, name):
            return getattr(self.local_db, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
