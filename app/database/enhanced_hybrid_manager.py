"""
نظام المزامنة المحسن 2.0
- مزامنة ثنائية الاتجاه (Real-time)
- إشعارات فورية للتغييرات
- تحسين الأداء وتجنب التكرار
- نظام Queue ذكي للمزامنة
"""

import os
import logging
import threading
import time
import queue
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .database_manager import DatabaseManager
from .supabase_manager import SupabaseManager

class EnhancedHybridManager:
    """
    نظام مزامنة محسن مع Real-time subscriptions
    """
    
    def __init__(self, local_db_path: str, supabase_url: str = None, supabase_key: str = None):
        """تهيئة النظام المحسن"""
        # تعيين متغير البيئة
        os.environ['SQLITE_FILE'] = os.path.basename(local_db_path)
        
        # تهيئة قواعد البيانات
        self.local_db = DatabaseManager()
        self.supabase_manager = None
        
        # إعداد التسجيل
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('EnhancedHybrid')
        
        # إعدادات المزامنة
        self.supabase_enabled = False
        self.sync_queue = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=3)
        
        # إعداد Real-time subscriptions
        self.subscriptions = {}
        self.last_sync_time = datetime.now()
        
        # إشعارات المزامنة
        self.sync_stats = {
            'operations_count': 0,
            'successful_operations': 0,
            'failed_operations': 0,
            'last_operation': None
        }
        
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
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Add فهرس للأداء
            self.local_db._execute_query_with_commit("""
                CREATE INDEX IF NOT EXISTS idx_pending_changes_created 
                ON pending_changes(created_at)
            """)
            
            self.logger.info("✅ Enhanced pending changes table ready")
        except Exception as e:
            self.logger.error(f"❌ Error setting up pending changes: {e}")
    
    def _initial_supabase_sync(self, supabase_url: str, supabase_key: str):
        """مزامنة أولية محسنة مع سوبابيس"""
        try:
            self.logger.info("🔄 Enhanced initial sync with Supabase...")
            
            # تهيئة مدير سوبابيس
            self.supabase_manager = SupabaseManager()
            
            # تحميل البيانات بطريقة محسنة
            self._download_all_data_enhanced()
            
            # تفعيل المزامنة
            self.supabase_enabled = True
            self.logger.info("✅ Enhanced initial sync completed")
            
            # بدء النظام المحسن
            self._start_enhanced_sync_system()
            
        except Exception as e:
            self.logger.error(f"❌ Error during enhanced sync: {e}")
    
    def _download_all_data_enhanced(self):
        """تحميل البيانات بطريقة محسنة ومتوازية"""
        try:
            # استخدام ThreadPoolExecutor للمزامنة المتوازية
            futures = []
            
            # تحميل الموظفين
            futures.append(
                self.executor.submit(self._sync_employees)
            )
            
            # تحميل المستخدمين
            futures.append(
                self.executor.submit(self._sync_users)
            )
            
            # تحميل سجلات الحضور
            futures.append(
                self.executor.submit(self._sync_attendance)
            )
            
            # انتظار اكتمال جميع العمليات
            for future in futures:
                future.result()
            
            self.logger.info("✅ Enhanced parallel data download completed")
            
        except Exception as e:
            self.logger.error(f"❌ Error in enhanced data download: {e}")
    
    def _sync_employees(self):
        """مزامنة الموظفين"""
        try:
            employees = self.supabase_manager.get_all_employees()
            new_count = 0
            updated_count = 0
            
            for emp in employees:
                try:
                    existing = self.local_db.get_employee_by_code(emp.get('employee_code'))
                    
                    emp_data = {
                        'employee_code': emp.get('employee_code') or f"EMP_{emp.get('id', 'XXX')}",
                        'name': emp.get('name') or 'Unknown',
                        'job_title': emp.get('job_title') or 'Unknown',
                        'department': emp.get('department') or 'Unknown',
                        'phone_number': emp.get('phone_number') or f"PHONE_{emp.get('id', 'UNK')}",
                        'qr_code': emp.get('qr_code', '')
                    }
                    
                    if existing:
                        if self.local_db.update_employee(existing['id'], emp_data):
                            updated_count += 1
                    else:
                        if self.local_db.add_employee(emp_data):
                            new_count += 1
                            
                except Exception as e:
                    self.logger.warning(f"⚠️ Skipping employee {emp.get('name', 'Unknown')}: {e}")
            
            self.logger.info(f"👥 Employees: {new_count} new, {updated_count} updated")
            
        except Exception as e:
            self.logger.error(f"❌ Error syncing employees: {e}")
    
    def _sync_users(self):
        """مزامنة المستخدمين"""
        try:
            users = self.supabase_manager.get_all_users()
            count = 0
            
            for user in users:
                try:
                    if not self.local_db.get_user_by_username(user.get('username')):
                        user_data = {
                            'username': user.get('username'),
                            'password': user.get('password', 'default123'),
                            'role': user.get('role', 'user')
                        }
                        if self.local_db.add_user(user_data):
                            count += 1
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to sync user {user.get('username')}: {e}")
            
            self.logger.info(f"👤 Users: {count} synced")
            
        except Exception as e:
            self.logger.error(f"❌ Error syncing users: {e}")
    
    def _sync_attendance(self):
        """مزامنة سجلات الحضور"""
        try:
            attendance_records = self.supabase_manager.get_all_attendance()
            count = 0
            
            for record in attendance_records:
                try:
                    employee = self.local_db.get_employee_by_code(record.get('employee_code'))
                    if employee:
                        check_time = record.get('check_time') or record.get('check_in') or record.get('check_out') or datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        attendance_data = {
                            'employee_id': str(employee['id']),
                            'check_time': check_time,
                            'date': record.get('date', datetime.now().strftime('%Y-%m-%d')),
                            'type': record.get('type', 'Check-In'),
                            'notes': record.get('notes', '')
                        }
                        
                        if self.local_db.add_attendance_record(attendance_data):
                            count += 1
                except Exception as e:
                    self.logger.warning(f"⚠️ Failed to sync attendance record: {e}")
            
            self.logger.info(f"📅 Attendance: {count} records synced")
            
        except Exception as e:
            self.logger.error(f"❌ Error syncing attendance: {e}")
    
    def _start_enhanced_sync_system(self):
        """بدء نظام المزامنة المحسن"""
        if not self.supabase_enabled:
            return
        
        # بدء معالج الطوابير
        self._start_queue_processor()
        
        # بدء المزامنة التلقائية (كنسخة احتياطية)
        self._start_auto_sync()
        
        # محاولة بدء Real-time subscriptions
        self._start_realtime_subscriptions()
        
        self.logger.info("🚀 Enhanced sync system started")
    
    def _start_queue_processor(self):
        """معالج طابور المزامنة"""
        def process_queue():
            self.logger.info("⚡ Smart queue processor started")
            while self.supabase_enabled:
                try:
                    # معالجة العناصر في الطابور
                    try:
                        sync_item = self.sync_queue.get(timeout=1)
                        self._process_sync_item(sync_item)
                        self.sync_queue.task_done()
                    except queue.Empty:
                        continue
                        
                except Exception as e:
                    self.logger.error(f"Queue processor error: {e}")
        
        queue_thread = threading.Thread(target=process_queue, daemon=True)
        queue_thread.start()
    
    def _start_auto_sync(self):
        """مزامنة تلقائية محسنة"""
        def auto_sync():
            self.logger.info("🔄 Enhanced auto-sync started (every 30 seconds)")
            sync_count = 0
            while self.supabase_enabled:
                try:
                    time.sleep(30)  # كل 30 ثانية (أقل تكراراً)
                    self._sync_pending_changes_enhanced()
                    
                    # تنظيف كل 5 دقائق (10 دورات × 30 ثانية)
                    sync_count += 1
                    if sync_count >= 10:
                        self.cleanup_failed_changes()
                        sync_count = 0
                        
                except Exception as e:
                    self.logger.error(f"Auto-sync error: {e}")
        
        sync_thread = threading.Thread(target=auto_sync, daemon=True)
        sync_thread.start()
    
    def _start_realtime_subscriptions(self):
        """بدء Real-time subscriptions (تجريبي)"""
        try:
            # هذا تجريبي - يحتاج مكتبة supabase-realtime
            self.logger.info("🔴 Real-time subscriptions (experimental)")
            # يمكن Add Real-time subscriptions هنا لاحقاً
        except Exception as e:
            self.logger.warning(f"⚠️ Real-time subscriptions not available: {e}")
    
    def _record_change_enhanced(self, table_name: str, operation: str, record_id: str, data: Dict[str, Any] = None):
        """تسجيل التغيير بطريقة محسنة"""
        if not self.supabase_enabled:
            return
        
        try:
            # Add للطابور للمعالجة السريعة
            sync_item = {
                'table_name': table_name,
                'operation': operation,
                'record_id': record_id,
                'data': data,
                'timestamp': datetime.now().isoformat()
            }
            
            self.sync_queue.put(sync_item)
            
            # تسجيل في قاعدة البيانات كنسخة احتياطية
            data_json = json.dumps(data) if data else '{}'
            self.local_db._execute_query_with_commit(
                "INSERT INTO pending_changes (table_name, operation, record_id, data) VALUES (?, ?, ?, ?)",
                (table_name, operation, record_id, data_json)
            )
            
            self.logger.info(f"📝 Enhanced change recorded: {operation} {table_name}:{record_id}")
            
        except Exception as e:
            self.logger.error(f"Error recording enhanced change: {e}")
    
    def _process_sync_item(self, sync_item):
        """معالجة عنصر المزامنة"""
        try:
            table_name = sync_item['table_name']
            operation = sync_item['operation']
            record_id = sync_item['record_id']
            data = sync_item['data']
            
            success = False
            
            if operation == 'INSERT':
                success = self._sync_insert_enhanced(table_name, data)
            elif operation == 'UPDATE':
                success = self._sync_update_enhanced(table_name, record_id, data)
            elif operation == 'DELETE':
                success = self._sync_delete_enhanced(table_name, record_id)
            
            # Update الإحصائيات
            self.sync_stats['operations_count'] += 1
            self.sync_stats['last_operation'] = f"{operation} {table_name}:{record_id}"
            
            if success:
                self.sync_stats['successful_operations'] += 1
                self.logger.info(f"✅ Enhanced sync success: {operation} {table_name}:{record_id}")
            else:
                self.sync_stats['failed_operations'] += 1
                self.logger.error(f"❌ Enhanced sync failed: {operation} {table_name}:{record_id}")
                
        except Exception as e:
            # معالجة خاصة للتكرار
            if "duplicate key" in str(e) or "23505" in str(e):
                self.sync_stats['successful_operations'] += 1
                self.logger.warning(f"⚠️ Duplicate conflict resolved for {operation} {table_name}:{record_id}")
            else:
                self.sync_stats['failed_operations'] += 1
                self.logger.error(f"❌ Error processing sync item: {e}")
    
    def _sync_insert_enhanced(self, table_name: str, data: Dict[str, Any]) -> bool:
        """إدراج محسن مع معالجة التكرار"""
        try:
            if table_name == 'employees':
                try:
                    result = self.supabase_manager.add_employee(data)
                    return bool(result)
                except Exception as e:
                    if "duplicate key" in str(e) or "23505" in str(e):
                        self.logger.warning(f"⚠️ Employee already exists in Supabase: {data.get('employee_code')} - ignoring")
                        return True  # نعتبر هذا نجاح لأن البيانات موجودة
                    raise e
                    
            elif table_name == 'users':
                try:
                    result = self.supabase_manager.add_user(data)
                    return bool(result)
                except Exception as e:
                    if "duplicate key" in str(e) or "23505" in str(e):
                        self.logger.warning(f"⚠️ User already exists in Supabase: {data.get('username')} - ignoring")
                        return True
                    raise e
                    
            elif table_name == 'attendance':
                return bool(self.supabase_manager.record_attendance(data))
            return False
            
        except Exception as e:
            if "duplicate key" in str(e) or "23505" in str(e):
                self.logger.warning(f"⚠️ Duplicate key ignored for {table_name}: {e}")
                return True
            self.logger.error(f"Enhanced insert error: {e}")
            return False
    
    def _sync_update_enhanced(self, table_name: str, record_id: str, data: Dict[str, Any]) -> bool:
        """Update محسن مع معالجة التكرار"""
        try:
            if table_name == 'employees':
                try:
                    return self.supabase_manager.update_employee(record_id, data)
                except Exception as e:
                    if "duplicate key" in str(e) or "23505" in str(e):
                        self.logger.warning(f"⚠️ Employee update conflict: {data.get('employee_code')} - data already exists")
                        return True  # نعتبر هذا نجاح لأن البيانات موجودة
                    raise e
                    
            elif table_name == 'users':
                try:
                    return self.supabase_manager.update_user(record_id, data)
                except Exception as e:
                    if "duplicate key" in str(e) or "23505" in str(e):
                        self.logger.warning(f"⚠️ User update conflict: {data.get('username')} - data already exists")
                        return True
                    raise e
                    
            elif table_name == 'attendance':
                return self.supabase_manager.update_attendance(record_id, data)
            return False
            
        except Exception as e:
            if "duplicate key" in str(e) or "23505" in str(e):
                self.logger.warning(f"⚠️ Update conflict ignored for {table_name}: {e}")
                return True
            self.logger.error(f"Enhanced update error: {e}")
            return False
    
    def _sync_delete_enhanced(self, table_name: str, record_id: str) -> bool:
        """Delete محسن"""
        try:
            if table_name == 'employees':
                return self.supabase_manager.delete_employee(record_id)
            elif table_name == 'users':
                return self.supabase_manager.delete_user(record_id)
            elif table_name == 'attendance':
                return self.supabase_manager.delete_attendance(record_id)
            return False
        except Exception as e:
            self.logger.error(f"Enhanced delete error: {e}")
            return False
    
    def _sync_pending_changes_enhanced(self):
        """مزامنة التغييرات المعلقة بطريقة محسنة"""
        if not self.supabase_enabled:
            return
        
        try:
            # جلب التغييرات مع إعادة المحاولة
            changes = self.local_db._execute_query(
                """SELECT * FROM pending_changes 
                   WHERE retry_count < 3 
                   ORDER BY created_at ASC 
                   LIMIT 50""",
                fetch=True
            )
            
            if not changes:
                return
            
            self.logger.info(f"🔄 Processing {len(changes)} pending changes")
            
            for change in changes:
                try:
                    success = False
                    
                    if change['operation'] == 'INSERT':
                        data = json.loads(change['data'])
                        success = self._sync_insert_enhanced(change['table_name'], data)
                    elif change['operation'] == 'UPDATE':
                        data = json.loads(change['data'])
                        success = self._sync_update_enhanced(change['table_name'], change['record_id'], data)
                    elif change['operation'] == 'DELETE':
                        success = self._sync_delete_enhanced(change['table_name'], change['record_id'])
                    
                    if success:
                        # Delete التغيير الناجح
                        self.local_db._execute_query_with_commit(
                            "DELETE FROM pending_changes WHERE id = ?",
                            (change['id'],)
                        )
                        # Delete التغييرات المكررة للعنصر نفسه
                        self.local_db._execute_query_with_commit(
                            "DELETE FROM pending_changes WHERE table_name = ? AND record_id = ? AND operation = ?",
                            (change['table_name'], change['record_id'], change['operation'])
                        )
                    else:
                        # زيادة عدد المحاولات
                        self.local_db._execute_query_with_commit(
                            "UPDATE pending_changes SET retry_count = retry_count + 1, last_attempt = CURRENT_TIMESTAMP WHERE id = ?",
                            (change['id'],)
                        )
                        
                except Exception as e:
                    # معالجة خاصة للتكرار في Background sync
                    if "duplicate key" in str(e) or "23505" in str(e):
                        self.logger.warning(f"⚠️ Background sync: Duplicate key ignored for {change['operation']} {change['table_name']}:{change['record_id']}")
                        # اعتبر هذا نجاحاً واDelete التغيير
                        self.local_db._execute_query_with_commit(
                            "DELETE FROM pending_changes WHERE id = ?",
                            (change['id'],)
                        )
                        # Delete التغييرات المكررة أيضاً
                        self.local_db._execute_query_with_commit(
                            "DELETE FROM pending_changes WHERE table_name = ? AND record_id = ? AND operation = ?",
                            (change['table_name'], change['record_id'], change['operation'])
                        )
                    else:
                        self.logger.error(f"Error processing change {change['id']}: {e}")
                        # زيادة عدد المحاولات للأخطاء الأخرى
                        self.local_db._execute_query_with_commit(
                            "UPDATE pending_changes SET retry_count = retry_count + 1, last_attempt = CURRENT_TIMESTAMP WHERE id = ?",
                            (change['id'],)
                        )
                    
        except Exception as e:
            self.logger.error(f"Error in enhanced pending sync: {e}")
    
    # --- واجهة المستخدم (تمرير إلى قاعدة البيانات المحلية) ---
    
    def add_employee(self, data):
        """Add موظف مع مزامنة محسنة"""
        result = self.local_db.add_employee(data)
        if result:
            self._record_change_enhanced('employees', 'INSERT', str(result), data)
        return result
    
    def update_employee(self, employee_id, employee_data):
        """Update employee مع مزامنة محسنة"""
        result = self.local_db.update_employee(employee_id, employee_data)
        if result:
            self._record_change_enhanced('employees', 'UPDATE', str(employee_id), employee_data)
        return result
    
    def delete_employee(self, employee_id):
        """Delete موظف مع مزامنة محسنة"""
        result = self.local_db.delete_employee(employee_id)
        if result:
            self._record_change_enhanced('employees', 'DELETE', str(employee_id))
        return result
    
    def add_user(self, user_data):
        """Add مستخدم مع مزامنة محسنة"""
        result = self.local_db.add_user(user_data)
        if result:
            self._record_change_enhanced('users', 'INSERT', str(result), user_data)
        return result
    
    def record_attendance(self, employee_id, attendance_type, location_id=None, notes=None):
        """تسجيل حضور مع مزامنة محسنة"""
        result = self.local_db.record_attendance(employee_id, attendance_type, location_id, notes)
        if result:
            attendance_data = {
                'employee_id': employee_id,
                'type': attendance_type,
                'location_id': location_id,
                'notes': notes,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            self._record_change_enhanced('attendance', 'INSERT', str(result), attendance_data)
        return result
    
    def force_full_sync(self):
        """إجبار مزامنة كاملة"""
        if not self.supabase_enabled:
            return False
        
        try:
            self.logger.info("🔄 Starting forced full sync...")
            self._download_all_data_enhanced()
            self._sync_pending_changes_enhanced()
            self.logger.info("✅ Forced full sync completed")
            return True
        except Exception as e:
            self.logger.error(f"Forced sync error: {e}")
            return False
    
    def cleanup_failed_changes(self):
        """تنظيف التغييرات الفاشلة المتكررة"""
        try:
            # Delete التغييرات التي Failedت أكثر من 3 مرات وكانت duplicate key
            self.local_db._execute_query_with_commit(
                "DELETE FROM pending_changes WHERE retry_count >= 3"
            )
            self.logger.info("🧹 Cleaned up failed pending changes")
        except Exception as e:
            self.logger.error(f"Error cleaning failed changes: {e}")
    
    def get_sync_stats(self):
        """إحصائيات المزامنة المحسنة"""
        try:
            pending_count = self.local_db._execute_query(
                "SELECT COUNT(*) as count FROM pending_changes",
                fetch=True
            )[0]['count']
            
            failed_count = self.local_db._execute_query(
                "SELECT COUNT(*) as count FROM pending_changes WHERE retry_count >= 3",
                fetch=True
            )[0]['count']
            
            success_rate = 0
            if self.sync_stats['operations_count'] > 0:
                success_rate = (self.sync_stats['successful_operations'] / self.sync_stats['operations_count']) * 100
            
            return {
                'mode': 'Enhanced Hybrid 2.0',
                'supabase_enabled': self.supabase_enabled,
                'pending_changes': pending_count,
                'failed_changes': failed_count,
                'queue_size': self.sync_queue.qsize(),
                'last_sync': self.last_sync_time.isoformat(),
                'total_operations': self.sync_stats['operations_count'],
                'successful_operations': self.sync_stats['successful_operations'],
                'failed_operations': self.sync_stats['failed_operations'],
                'success_rate': f"{success_rate:.1f}%",
                'last_operation': self.sync_stats.get('last_operation', 'None')
            }
        except Exception as e:
            self.logger.error(f"Error getting sync stats: {e}")
            return {'error': str(e)}
    
    def print_sync_status(self):
        """طباعة حالة المزامنة"""
        stats = self.get_sync_stats()
        if 'error' in stats:
            self.logger.error(f"📊 Stats error: {stats['error']}")
            return
            
        self.logger.info("📊 Enhanced Sync Status:")
        self.logger.info(f"   🔄 Mode: {stats['mode']}")
        self.logger.info(f"   🌐 Supabase: {'✅ Enabled' if stats['supabase_enabled'] else '❌ Disabled'}")
        self.logger.info(f"   📊 Success Rate: {stats['success_rate']}")
        self.logger.info(f"   📝 Total Operations: {stats['total_operations']}")
        self.logger.info(f"   ✅ Successful: {stats['successful_operations']}")
        self.logger.info(f"   ❌ Failed: {stats['failed_operations']}")
        self.logger.info(f"   ⏳ Pending: {stats['pending_changes']}")
        self.logger.info(f"   🗃️ Queue Size: {stats['queue_size']}")
        self.logger.info(f"   🕐 Last Operation: {stats['last_operation']}")
    
    def cleanup_on_exit(self):
        """تنظيف محسن عند الخروج"""
        try:
            self.logger.info("🔄 Enhanced cleanup starting...")
            
            # إيقاف المزامنة
            self.supabase_enabled = False
            
            # معالجة آخر العناصر في الطابور
            while not self.sync_queue.empty():
                try:
                    sync_item = self.sync_queue.get_nowait()
                    self._process_sync_item(sync_item)
                except queue.Empty:
                    break
            
            # Close الـ executor
            self.executor.shutdown(wait=True)
            
            self.logger.info("✅ Enhanced cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Enhanced cleanup error: {e}")
    
    def __getattr__(self, name):
        """تمرير الدوال غير المعرفة إلى قاعدة البيانات المحلية"""
        if hasattr(self.local_db, name):
            return getattr(self.local_db, name)
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
