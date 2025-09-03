#!/usr/bin/env python3
"""
مدير قاعدة البيانات الهجين البسيط - مزامنة فعالة مثل النسخة الأصلية
"""

import sqlite3
import threading
import time
import json
import queue
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from .database_manager import DatabaseManager
from .supabase_manager import SupabaseManager

import logging
logger = logging.getLogger('SimpleHybrid')

class SimpleHybridManager:
    def __init__(self):
        try:
            logger.info("🔄 تهيئة النظام الهجين - Supabase First...")
            
            self.local_db_path = "attendance.db"
            self.original_db = None  # لن ننشئه إلا عند الحاجة للمزامنة
            self.supabase_manager = None
            
            # 🚀 مزامنة فورية في الاتجاهين
            self.sync_interval = 2  # 2 ثانية للمزامنة الفورية
            self.supabase_sync_interval = 3  # 3 ثوانِ للمزامنة من Supabase
            
            # قائمة انتظار المزامنة
            self.sync_queue = queue.Queue()
            self.sync_running = True
            
            # قفل للعمليات المتزامنة
            self.db_lock = threading.Lock()
            
            # إعدادات المزامنة الفورية
            self.instant_sync = True
            self.supabase_first = True  # Supabase له الأولوية
            self.supabase_sync_thread_pool = []
            self.sync_thread_pool = []  # Add sync_thread_pool
            
            # إعدادات التحكم الكامل
            self.control_settings = {
                'sync_enabled': True,
                'instant_sync': True,
                'supabase_first': True,  # Supabase أولوية
                'auto_sync_interval': 2,
                'supabase_sync_interval': 3,
                'max_sync_threads': 15,
                'retry_failed_operations': True,
                'max_retry_count': 3,
                'log_level': 'INFO',
                'backup_enabled': True,
                'monitoring_enabled': True,
                'delete_local_on_exit': True  # Delete قاعدة البيانات المحلية عند الخروج
            }
            
            # إحصائيات مفصلة
            self.detailed_stats = {
                'total_operations': 0,
                'successful_operations': 0,
                'failed_operations': 0,
                'duplicate_operations': 0,
                'retry_operations': 0,
                'last_sync_time': None,
                'last_supabase_sync_time': None,
                'sync_errors': [],
                'performance_metrics': {}
            }
            
            # 🆕 نظام كشف التغييرات الذكي
            self.change_detection = {
                'enabled': True,
                'last_supabase_hash': None,
                'last_change_check': None,
                'change_check_interval': 60,  # 60 ثانية
                'has_changes': False,
                'change_count': 0,
                'last_change_time': None,
                'change_types': []  # أنواع التغييرات المكتشفة
            }
            
            logger.info("✅ تم تهيئة المتغيرات الأساسية")
            
            # 🚀 إعداد قاعدة البيانات المحلية
            self._setup_local_database()
            
            # 📥 تحميل البيانات من Supabase (أولوية قصوى) - في الخلفية
            try:
                self._load_data_from_supabase_priority()
            except Exception as e:
                logger.warning(f"⚠️ Failed في تحميل البيانات من Supabase: {e}")
                logger.info("🔄 سيتم استخدام قاعدة البيانات المحلية فقط")
            
            # 🆕 مزامنة إضافية للإعدادات من Supabase (ضمان المزامنة)
            try:
                logger.info("🔄 مزامنة إضافية للإعدادات من Supabase...")
                if self.supabase_manager:
                    self._sync_settings_from_supabase()
                    logger.info("✅ تمت المزامنة الإضافية للإعدادات")
                else:
                    logger.warning("⚠️ SupabaseManager غير متاح للمزامنة الإضافية")
            except Exception as e:
                logger.warning(f"⚠️ فشلت المزامنة الإضافية للإعدادات: {e}")
            
            # ⚡ بدء خيوط المزامنة الفورية - في الخلفية
            try:
                self._start_instant_sync_threads()
            except Exception as e:
                logger.warning(f"⚠️ Failed في بدء خيوط المزامنة: {e}")
                logger.info("🔄 سيتم استخدام المزامنة اليدوية فقط")
            
            logger.info("✅ تم تهيئة النظام الهجين - Supabase First بنجاح")
            
        except Exception as e:
            logger.error(f"❌ Failed في تهيئة النظام الهجين: {e}")
            raise
    
    def _setup_local_database(self):
        """إعداد قاعدة البيانات المحلية"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # جدول الموظفين
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_code TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    job_title TEXT,
                    department TEXT,
                    phone_number TEXT UNIQUE,
                    qr_code TEXT,
                    fingerprint_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول المستخدمين
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT DEFAULT 'Viewer',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول الحضور
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    check_time TIMESTAMP,
                    date DATE NOT NULL,
                    type TEXT DEFAULT 'Check-In',
                    notes TEXT,
                    location_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees (id)
                )
            ''')
            
            # جدول المزامنة
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT NOT NULL,
                    record_id INTEGER NOT NULL,
                    operation TEXT NOT NULL,
                    local_data TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    retry_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    synced_at TIMESTAMP
                )
            ''')
            
            # جدول إعدادات التطبيق
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جداول إضافية للتوافق
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    radius_meters INTEGER NOT NULL
                )
            ''')
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS holidays (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    description TEXT NOT NULL,
                    date TEXT NOT NULL UNIQUE
                )
            ''')
            
            # إنشاء فهارس لتحسين الأداء
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_employees_code ON employees(employee_code)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_employees_name ON employees(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_employee ON attendance(employee_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sync_queue_status ON sync_queue(status)')
            
            conn.commit()
            conn.close()
            logger.info("✅ تم إعداد قاعدة البيانات المحلية")
            
        except Exception as e:
            logger.error(f"❌ Failed في إعداد قاعدة البيانات المحلية: {e}")
    
    def _load_data_from_supabase_priority(self):
        """تحميل البيانات من Supabase بأولوية قصوى - Supabase First"""
        try:
            logger.info("🚀 تحميل البيانات من Supabase بأولوية قصوى...")
            
            # إنشاء SupabaseManager فوراً
            if self.supabase_manager is None:
                self.supabase_manager = SupabaseManager()
            
            # 📥 تحميل الموظفين (أولوية قصوى)
            try:
                logger.info("📥 جاري تحميل الموظفين من Supabase...")
                employees = self.supabase_manager.get_all_employees()
                if employees:
                    conn = sqlite3.connect(self.local_db_path)
                    cursor = conn.cursor()
                    
                    # مسح البيانات المحلية أولاً
                    cursor.execute('DELETE FROM employees')
                    
                    for employee in employees:
                        cursor.execute('''
                            INSERT INTO employees 
                            (id, employee_code, name, job_title, department, phone_number, web_fingerprint, device_token, qr_code, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ''', (
                            employee.get('id'), 
                            employee.get('employee_code') or f"EMP_{employee.get('id')}", 
                            employee.get('name') or 'Unknown', 
                            employee.get('job_title', ''),
                            employee.get('department', ''),
                            employee.get('phone_number') or f"PHONE_{employee.get('id')}",
                            employee.get('web_fingerprint', ''),
                            employee.get('device_token', ''),
                            employee.get('qr_code', '')
                        ))
                    
                    conn.commit()
                    conn.close()
                    logger.info(f"✅ تم تحميل {len(employees)} موظف من Supabase")
                else:
                    logger.warning("⚠️ لا توجد موظفين في Supabase")
            except Exception as e:
                logger.error(f"❌ Error في تحميل الموظفين: {e}")
            
            # 📥 تحميل المستخدمين
            try:
                logger.info("📥 جاري تحميل المستخدمين من Supabase...")
                users = self.supabase_manager.get_all_users()
                if users:
                    conn = sqlite3.connect(self.local_db_path)
                    cursor = conn.cursor()
                    
                    # مسح البيانات المحلية أولاً
                    cursor.execute('DELETE FROM users')
                    
                    for user in users:
                        try:
                            cursor.execute('''
                                INSERT INTO users (id, username, password, role)
                                VALUES (?, ?, ?, ?)
                            ''', (
                                user.get('id'), 
                                user.get('username'), 
                                user.get('password', ''), 
                                user.get('role', 'Viewer')
                            ))
                        except Exception as e:
                            logger.warning(f"⚠️ Error في تحميل مستخدم {user.get('username')}: {e}")
                            continue
                    
                    conn.commit()
                    conn.close()
                    logger.info(f"✅ تم تحميل {len(users)} مستخدم من Supabase")
                else:
                    logger.warning("⚠️ لا توجد مستخدمين في Supabase")
            except Exception as e:
                logger.error(f"❌ Error في تحميل المستخدمين: {e}")
            
            # 📥 تحميل بيانات الحضور
            try:
                logger.info("📥 جاري تحميل سجلات الحضور من Supabase...")
                attendance_records = self.supabase_manager.get_all_attendance()
                if attendance_records:
                    conn = sqlite3.connect(self.local_db_path)
                    cursor = conn.cursor()
                    
                    # مسح البيانات المحلية أولاً
                    cursor.execute('DELETE FROM attendance')
                    
                    for record in attendance_records:
                        try:
                            cursor.execute('''
                                INSERT INTO attendance 
                                (id, employee_id, check_time, date, type, notes, location_id)
                                VALUES (?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                record.get('id'),
                                record.get('employee_id'),
                                record.get('check_time'),
                                record.get('date'),
                                record.get('type', 'Check-In'),
                                record.get('notes', ''),
                                record.get('location_id')
                            ))
                        except Exception as e:
                            logger.warning(f"⚠️ Error في تحميل سجل حضور: {e}")
                            continue
                    
                    conn.commit()
                    conn.close()
                    logger.info(f"✅ تم تحميل {len(attendance_records)} سجل حضور من Supabase")
                else:
                    logger.warning("⚠️ لا توجد سجلات حضور في Supabase")
            except Exception as e:
                logger.error(f"❌ Error في تحميل سجلات الحضور: {e}")
            
            # 📥 تحميل المواقع
            try:
                logger.info("📥 جاري تحميل المواقع من Supabase...")
                locations = self.supabase_manager.get_all_locations()
                if locations:
                    conn = sqlite3.connect(self.local_db_path)
                    cursor = conn.cursor()
                    
                    # مسح البيانات المحلية أولاً
                    cursor.execute('DELETE FROM locations')
                    
                    for location in locations:
                        try:
                            cursor.execute('''
                                INSERT INTO locations (id, name, latitude, longitude, radius_meters)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (
                                location.get('id'),
                                location.get('name', ''),
                                location.get('latitude', 0.0),
                                location.get('longitude', 0.0),
                                location.get('radius_meters', 100)
                            ))
                        except Exception as e:
                            logger.warning(f"⚠️ Error في تحميل موقع {location.get('name')}: {e}")
                            continue
                    
                    conn.commit()
                    conn.close()
                    logger.info(f"✅ تم تحميل {len(locations)} موقع من Supabase")
                else:
                    logger.warning("⚠️ لا توجد مواقع في Supabase")
            except Exception as e:
                logger.error(f"❌ Error في تحميل المواقع: {e}")
            
            # 📥 تحميل الإجازات
            try:
                logger.info("📥 جاري تحميل الإجازات من Supabase...")
                holidays = self.supabase_manager.get_all_holidays()
                if holidays:
                    conn = sqlite3.connect(self.local_db_path)
                    cursor = conn.cursor()
                    
                    # مسح البيانات المحلية أولاً
                    cursor.execute('DELETE FROM holidays')
                    
                    for holiday in holidays:
                        try:
                            cursor.execute('''
                                INSERT INTO holidays (id, description, date)
                                VALUES (?, ?, ?)
                            ''', (
                                holiday.get('id'),
                                holiday.get('description', ''),
                                holiday.get('date', '')
                            ))
                        except Exception as e:
                            logger.warning(f"⚠️ Error في تحميل إجازة {holiday.get('description')}: {e}")
                            continue
                    
                    conn.commit()
                    conn.close()
                    logger.info(f"✅ تم تحميل {len(holidays)} إجازة من Supabase")
                else:
                    logger.warning("⚠️ لا توجد إجازات في Supabase")
            except Exception as e:
                logger.error(f"❌ Error في تحميل الإجازات: {e}")
            
            # 📥 تحميل الإعدادات
            try:
                logger.info("📥 جاري تحميل الإعدادات من Supabase...")
                
                # محاولة مزامنة الإعدادات من Supabase أولاً
                try:
                    self._sync_settings_from_supabase()
                    logger.info("✅ تم مزامنة الإعدادات من Supabase")
                except Exception as e:
                    logger.warning(f"⚠️ فشلت مزامنة الإعدادات من Supabase: {e}")
                    logger.info("🔄 سيتم إنشاء إعدادات افتراضية محلياً")
                    
                    # إنشاء إعدادات افتراضية إذا فشلت المزامنة
                    default_settings = {
                        'theme': 'light',
                        'language': 'ar',
                        'auto_backup': 'true',
                        'sync_interval': '30',
                        'work_start_time': '08:00',
                        'late_allowance_minutes': '15',
                        'auto_sync': 'true'
                    }
                    
                    conn = sqlite3.connect(self.local_db_path)
                    cursor = conn.cursor()
                    
                    # مسح الإعدادات المحلية أولاً
                    cursor.execute('DELETE FROM app_settings')
                    
                    for key, value in default_settings.items():
                        cursor.execute('''
                            INSERT INTO app_settings (key, value)
                            VALUES (?, ?)
                        ''', (key, value))
                    
                    conn.commit()
                    conn.close()
                    logger.info(f"✅ تم إنشاء {len(default_settings)} إعداد افتراضي")
                    
            except Exception as e:
                logger.error(f"❌ Error في تحميل الإعدادات: {e}")
            
            # Update وقت آخر مزامنة
            self.detailed_stats['last_supabase_sync_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # 🆕 مزامنة نهائية للإعدادات من Supabase
            try:
                logger.info("🔄 مزامنة نهائية للإعدادات من Supabase...")
                self._sync_settings_from_supabase()
                logger.info("✅ تمت المزامنة النهائية للإعدادات")
            except Exception as e:
                logger.warning(f"⚠️ فشلت المزامنة النهائية للإعدادات: {e}")
            
            logger.info("🚀 تم تحميل جميع البيانات من Supabase بأولوية قصوى!")
            logger.info("📊 قاعدة البيانات المحلية محدثة بالكامل من Supabase")
            
        except Exception as e:
            logger.error(f"❌ Failed في تحميل البيانات من Supabase: {e}")
            raise
    
    def _start_instant_sync_threads(self):
        """بدء خيوط المزامنة الفورية - Supabase First"""
        try:
            # 🚀 خيط المزامنة من البرنامج إلى Supabase (كل 2 ثانية)
            self.sync_thread = threading.Thread(target=self._sync_worker, daemon=True)
            self.sync_thread.start()
            logger.info("⚡ بدء خيط المزامنة الفورية (كل 2 ثانية)")
            
            # 📥 خيط المزامنة من Supabase إلى البرنامج (كل 3 ثوان)
            self.supabase_sync_thread = threading.Thread(target=self._supabase_sync_worker, daemon=True)
            self.supabase_sync_thread.start()
            logger.info("📥 بدء خيط المزامنة من Supabase (كل 3 ثوان)")
            
            # 🔄 خيط المزامنة الفورية للعمليات
            self.instant_sync_thread = threading.Thread(target=self._instant_sync_worker, daemon=True)
            self.instant_sync_thread.start()
            logger.info("🔄 بدء خيط المزامنة الفورية للعمليات")
            
        except Exception as e:
            logger.error(f"❌ Error في بدء خيوط المزامنة: {e}")
            raise
    
    def _sync_worker(self):
        """عامل المزامنة الفورية من البرنامج إلى Supabase"""
        while self.sync_running:
            try:
                # معالجة قائمة انتظار المزامنة (من البرنامج إلى Supabase)
                self._process_sync_queue()
                
                # معالجة قائمة انتظار الذاكرة
                self._process_memory_queue()
                
                # انتظار قصير للمزامنة الفورية
                time.sleep(self.sync_interval)
                
            except Exception as e:
                logger.error(f"❌ Error في المزامنة إلى Supabase: {e}")
                time.sleep(1)  # انتظار أقل في حالة الError
    
    def _supabase_sync_worker(self):
        """عامل المزامنة الفورية من Supabase إلى البرنامج"""
        while self.sync_running:
            try:
                # مزامنة فورية من Supabase (كل 3 ثوان)
                self._sync_from_supabase_to_local()
                
                # انتظار قصير للمزامنة الفورية
                time.sleep(self.supabase_sync_interval)
                
            except Exception as e:
                logger.error(f"❌ Error في المزامنة من Supabase: {e}")
                time.sleep(1)  # انتظار أقل في حالة الError
    
    def _instant_sync_worker(self):
        """عامل المزامنة الفورية للعمليات"""
        while self.sync_running:
            try:
                # معالجة العمليات الفورية
                self._process_instant_operations()
                
                # انتظار قصير
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error في المزامنة الفورية: {e}")
                time.sleep(1)
    
    def _process_instant_operations(self):
        """معالجة العمليات الفورية"""
        try:
            # معالجة العمليات العاجلة
            pass
        except Exception as e:
            logger.error(f"❌ Error في معالجة العمليات الفورية: {e}")
    
    def _process_sync_queue(self):
        """معالجة قائمة انتظار المزامنة من قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, table_name, record_id, operation, local_data, retry_count
                FROM sync_queue 
                WHERE status = 'pending' AND retry_count < 3
                ORDER BY created_at ASC
                LIMIT 20
            ''')
            
            records = cursor.fetchall()
            
            if records:
                logger.info(f"🔄 معالجة {len(records)} عملية مزامنة معلقة...")
            
            for record in records:
                queue_id, table_name, record_id, operation, local_data, retry_count = record
                
                try:
                    data = json.loads(local_data) if local_data else {}
                    success = self._sync_record(table_name, record_id, operation, data)
                    
                    if success:
                        # Update الحالة إلى مزامن
                        cursor.execute('''
                            UPDATE sync_queue 
                            SET status = 'synced', synced_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (queue_id,))
                        logger.info(f"✅ تم مزامنة {operation} لجدول {table_name}")
                    else:
                        # زيادة عدد المحاولات
                        cursor.execute('''
                            UPDATE sync_queue 
                            SET retry_count = retry_count + 1
                            WHERE id = ?
                        ''', (queue_id,))
                        logger.warning(f"⚠️ Failed في مزامنة {operation} لجدول {table_name}")
                    
                except Exception as e:
                    # معالجة التكرار
                    if "duplicate key" in str(e) or "23505" in str(e):
                        logger.warning(f"⚠️ تجاهل تكرار في {operation} لجدول {table_name}")
                        cursor.execute('''
                            UPDATE sync_queue 
                            SET status = 'synced', synced_at = CURRENT_TIMESTAMP
                            WHERE id = ?
                        ''', (queue_id,))
                    else:
                        logger.error(f"❌ Error في مزامنة {operation}: {e}")
                        cursor.execute('''
                            UPDATE sync_queue 
                            SET retry_count = retry_count + 1
                            WHERE id = ?
                        ''', (queue_id,))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error في معالجة قائمة المزامنة: {e}")
    
    def _process_memory_queue(self):
        """معالجة قائمة انتظار الذاكرة"""
        try:
            while not self.sync_queue.empty():
                record = self.sync_queue.get_nowait()
                table_name, record_id, operation, data = record
                
                # Add إلى قاعدة البيانات للمزامنة الدورية
                self._add_to_sync_queue(table_name, record_id, operation, data)
                logger.info(f"📝 تم Add {operation} لجدول {table_name} لقائمة المزامنة")
                
        except queue.Empty:
            pass
        except Exception as e:
            logger.error(f"❌ Error في معالجة قائمة الذاكرة: {e}")
    
    def _sync_record(self, table_name: str, record_id: int, operation: str, data: Dict) -> bool:
        """مزامنة سجل واحد مع Supabase"""
        try:
            # إنشاء SupabaseManager فقط عند الحاجة
            if self.supabase_manager is None:
                self.supabase_manager = SupabaseManager()
            
            if table_name == "employees":
                if operation == "INSERT":
                    return bool(self.supabase_manager.add_employee(data))
                elif operation == "UPDATE":
                    return self.supabase_manager.update_employee(record_id, data)
                elif operation == "DELETE":
                    return self.supabase_manager.delete_employee(record_id)
            
            elif table_name == "users":
                if operation == "INSERT":
                    return bool(self.supabase_manager.add_user(data))
                elif operation == "UPDATE":
                    return self.supabase_manager.update_user(record_id, data)
                elif operation == "DELETE":
                    return self.supabase_manager.delete_user(record_id)
            
            elif table_name == "attendance":
                if operation == "INSERT":
                    # تحقق من وجود الموظف أولاً
                    if not self._employee_exists_in_supabase(data.get('employee_id')):
                        logger.warning(f"⚠️ الموظف غير موجود في Supabase، تخطي تسجيل الحضور")
                        return False
                    return bool(self.supabase_manager.record_attendance(data))
                elif operation == "UPDATE":
                    return self.supabase_manager.update_attendance(record_id, data)
                elif operation == "DELETE":
                    return self.supabase_manager.delete_attendance(record_id)
            
            elif table_name == "locations":
                if operation == "INSERT":
                    return bool(self.supabase_manager.add_location(data))
                elif operation == "UPDATE":
                    return self.supabase_manager.update_location(record_id, data)
                elif operation == "DELETE":
                    return self.supabase_manager.delete_location(record_id)
            
            elif table_name == "holidays":
                if operation == "INSERT":
                    return bool(self.supabase_manager.add_holiday(data))
                elif operation == "UPDATE":
                    return self.supabase_manager.update_holiday(record_id, data)
                elif operation == "DELETE":
                    return self.supabase_manager.delete_holiday(record_id)
            
            return True
            
        except Exception as e:
            # معالجة أخطاء التكرار
            if "duplicate key" in str(e) or "23505" in str(e):
                logger.warning(f"⚠️ تجاهل تكرار في {operation} لجدول {table_name}: {e}")
                return True
            # معالجة أخطاء المفاتيح الخارجية
            if "foreign key constraint" in str(e) or "23503" in str(e):
                logger.warning(f"⚠️ مشكلة مفتاح خارجي في {operation} لجدول {table_name}: {e}")
                return False
            logger.error(f"❌ Failed في مزامنة {operation} لجدول {table_name}: {e}")
            return False
    
    def _employee_exists_in_supabase(self, employee_id: int) -> bool:
        """التحقق من وجود الموظف في Supabase"""
        try:
            if self.supabase_manager is None:
                self.supabase_manager = SupabaseManager()
            
            employees = self.supabase_manager.get_all_employees()
            return any(emp.get('id') == employee_id for emp in employees)
        except Exception:
            return False
    
    def _add_to_sync_queue(self, table_name: str, record_id: int, operation: str, data: Dict):
        """Add إلى قائمة انتظار المزامنة بدون تأخير"""
        try:
            # محاولة واحدة فقط مع timeout قصير
            conn = sqlite3.connect(self.local_db_path, timeout=0.5)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO sync_queue (table_name, record_id, operation, local_data)
                VALUES (?, ?, ?, ?)
            ''', (table_name, record_id, operation, json.dumps(data)))
            
            conn.commit()
            conn.close()
            return True
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                # Add إلى قائمة الذاكرة بدلاً من الانتظار
                self.sync_queue.put((table_name, record_id, operation, data))
                logger.info(f"📝 تم Add {operation} لجدول {table_name} لقائمة الذاكرة (تجنب القفل)")
                return True
            else:
                logger.warning(f"⚠️ Error في قاعدة البيانات: {e}")
                return False
        except Exception as e:
            logger.warning(f"⚠️ Error في Add إلى قائمة المزامنة: {e}")
            # Add إلى قائمة الذاكرة كبديل
            self.sync_queue.put((table_name, record_id, operation, data))
            return True
    
    def _immediate_sync(self, table_name: str, record_id: int, operation: str, data: Dict):
        """مزامنة فورية للعملية بدون انتظار"""
        if not self.instant_sync:
            return
            
        def sync_in_background():
            try:
                # تأخير قصير لتجنب التداخل مع العملية المحلية
                time.sleep(0.1)
                
                success = self._sync_record(table_name, record_id, operation, data)
                if success:
                    logger.info(f"⚡ مزامنة فورية ناجحة: {operation} {table_name}:{record_id}")
                    # محاولة Delete من قائمة المزامنة بدون انتظار
                    self._remove_from_sync_queue_fast(table_name, record_id, operation)
                else:
                    logger.warning(f"⚠️ Failed في المزامنة الفورية: {operation} {table_name}:{record_id}")
            except Exception as e:
                logger.error(f"❌ Error في المزامنة الفورية: {e}")
        
        # فحص عدد الخيوط المسموح
        active_threads = [t for t in self.sync_thread_pool if t.is_alive()]
        max_threads = self.control_settings.get('max_sync_threads', 10)
        
        if len(active_threads) < max_threads:
            # تشغيل المزامنة في خيط منفصل
            sync_thread = threading.Thread(target=sync_in_background, daemon=True)
            sync_thread.start()
            self.sync_thread_pool.append(sync_thread)
        else:
            # Add إلى قائمة الذاكرة إذا كانت الخيوط ممتلئة
            self.sync_queue.put((table_name, record_id, operation, data))
            logger.info(f"📝 تم Add {operation} لقائمة الذاكرة (الخيوط ممتلئة)")
        
        # تنظيف الخيوط المنتهية
        self.sync_thread_pool = [t for t in self.sync_thread_pool if t.is_alive()]
    
    def _remove_from_sync_queue(self, table_name: str, record_id: int, operation: str):
        """Delete عملية من قائمة المزامنة بعد نجاحها"""
        try:
            conn = sqlite3.connect(self.local_db_path, timeout=10.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE sync_queue 
                SET status = 'synced', synced_at = CURRENT_TIMESTAMP
                WHERE table_name = ? AND record_id = ? AND operation = ? AND status = 'pending'
            ''', (table_name, record_id, operation))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error في Delete من قائمة المزامنة: {e}")
    
    def _remove_from_sync_queue_fast(self, table_name: str, record_id: int, operation: str):
        """Delete سريع من قائمة المزامنة بدون انتظار"""
        try:
            conn = sqlite3.connect(self.local_db_path, timeout=0.1)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE sync_queue 
                SET status = 'synced', synced_at = CURRENT_TIMESTAMP
                WHERE table_name = ? AND record_id = ? AND operation = ? AND status = 'pending'
            ''', (table_name, record_id, operation))
            
            conn.commit()
            conn.close()
            
        except sqlite3.OperationalError:
            # تجاهل إذا كانت قاعدة البيانات مقفلة
            pass
        except Exception:
            # تجاهل الأخطاء الأخرى
            pass
    
    # === دوال المزامنة من Supabase إلى البرنامج ===
    
    def _should_sync_from_supabase(self) -> bool:
        """تحديد ما إذا كان يجب المزامنة من Supabase"""
        try:
            # مزامنة فورية كل 3 ثوان (Supabase First)
            if not hasattr(self, '_last_supabase_sync'):
                self._last_supabase_sync = 0
            
            current_time = time.time()
            if current_time - self._last_supabase_sync >= self.supabase_sync_interval:
                self._last_supabase_sync = current_time
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Error في فحص توقيت المزامنة: {e}")
            return False
    
    def _sync_from_supabase_to_local(self):
        """مزامنة البيانات من Supabase إلى قاعدة البيانات المحلية"""
        try:
            if not self.supabase_manager:
                return
            
            logger.info("🔄 بدء المزامنة من Supabase إلى البرنامج...")
            
            # 1. مزامنة الموظفين
            self._sync_employees_from_supabase()
            
            # 2. مزامنة المستخدمين
            self._sync_users_from_supabase()
            
            # 3. مزامنة سجلات الحضور
            self._sync_attendance_from_supabase()
            
            # 4. مزامنة المواقع
            self._sync_locations_from_supabase()
            
            # 5. مزامنة الإجازات
            self._sync_holidays_from_supabase()
            
            # 6. مزامنة الإعدادات
            self._sync_settings_from_supabase()
            
            logger.info("✅ اكتملت المزامنة من Supabase إلى البرنامج")
            
            # 🆕 Update hash البيانات بعد المزامنة
            self.change_detection['last_supabase_hash'] = self._get_supabase_data_hash()
            self.change_detection['has_changes'] = False
            
        except Exception as e:
            logger.error(f"❌ Error في المزامنة من Supabase: {e}")
    
    def _sync_employees_from_supabase(self):
        """مزامنة الموظفين من Supabase"""
        try:
            # الحصول على الموظفين من Supabase
            supabase_employees = self.supabase_manager.get_all_employees()
            if not supabase_employees:
                return
            
            # الحصول على الموظفين المحليين
            local_employees = {emp['id']: emp for emp in self.get_all_employees()}
            
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            for supabase_emp in supabase_employees:
                emp_id = supabase_emp.get('id')
                if not emp_id:
                    continue
                
                if emp_id in local_employees:
                    # Update الموظف الموجود
                    local_emp = local_employees[emp_id]
                    if self._has_employee_changes(supabase_emp, local_emp):
                        self._update_local_employee(cursor, emp_id, supabase_emp)
                        logger.info(f"🔄 تم Update الموظف: {supabase_emp.get('name')}")
                else:
                    # Add new employee
                    self._add_local_employee(cursor, supabase_emp)
                    logger.info(f"➕ تم Add new employee: {supabase_emp.get('name')}")
            
            # Delete الموظفين المحذوفين من Supabase
            supabase_ids = {emp.get('id') for emp in supabase_employees}
            for local_id in local_employees:
                if local_id not in supabase_ids:
                    self._delete_local_employee(cursor, local_id)
                    logger.info(f"🗑️ تم Delete موظف محلي: {local_employees[local_id].get('name')}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error في مزامنة الموظفين من Supabase: {e}")
    
    def _sync_users_from_supabase(self):
        """مزامنة المستخدمين من Supabase"""
        try:
            # الحصول على المستخدمين من Supabase
            supabase_users = self.supabase_manager.get_all_users()
            if not supabase_users:
                return
            
            # الحصول على المستخدمين المحليين
            local_users = {user['id']: user for user in self.get_all_users()}
            
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            for supabase_user in supabase_users:
                user_id = supabase_user.get('id')
                if not user_id:
                    continue
                
                if user_id in local_users:
                    # Update المستخدم الموجود
                    local_user = local_users[user_id]
                    if self._has_user_changes(supabase_user, local_user):
                        self._update_local_user(cursor, user_id, supabase_user)
                        logger.info(f"🔄 تم Update المستخدم: {supabase_user.get('username')}")
                else:
                    # Add مستخدم جديد
                    self._add_local_user(cursor, supabase_user)
                    logger.info(f"➕ تم Add مستخدم جديد: {supabase_user.get('username')}")
            
            # Delete المستخدمين المحذوفين من Supabase
            supabase_ids = {user.get('id') for user in supabase_users}
            for local_id in local_users:
                if local_id not in supabase_ids:
                    self._delete_local_user(cursor, local_id)
                    logger.info(f"🗑️ تم Delete مستخدم محلي: {local_users[local_id].get('username')}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error في مزامنة المستخدمين من Supabase: {e}")
    
    def _sync_attendance_from_supabase(self):
        """مزامنة سجلات الحضور من Supabase"""
        try:
            # الحصول على سجلات الحضور من Supabase
            supabase_attendance = self.supabase_manager.get_all_attendance()
            if not supabase_attendance:
                return
            
            # الحصول على سجلات الحضور المحلية
            local_attendance = self._get_local_attendance_dict()
            
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            for supabase_record in supabase_attendance:
                record_id = supabase_record.get('id')
                if not record_id:
                    continue
                
                if record_id in local_attendance:
                    # Update السجل الموجود
                    local_record = local_attendance[record_id]
                    if self._has_attendance_changes(supabase_record, local_record):
                        self._update_local_attendance(cursor, record_id, supabase_record)
                        logger.info(f"🔄 تم Update سجل حضور: ID {record_id}")
                else:
                    # Add سجل جديد
                    self._add_local_attendance(cursor, supabase_record)
                    logger.info(f"➕ تم Add سجل حضور جديد: ID {record_id}")
            
            # Delete السجلات المحذوفة من Supabase
            supabase_ids = {record.get('id') for record in supabase_attendance}
            for local_id in local_attendance:
                if local_id not in supabase_ids:
                    self._delete_local_attendance(cursor, local_id)
                    logger.info(f"🗑️ تم Delete سجل حضور محلي: ID {local_id}")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Error في مزامنة سجلات الحضور من Supabase: {e}")
    
    def _sync_settings_from_supabase(self):
        """مزامنة الإعدادات من Supabase - محسنة ومحسنة"""
        try:
            if not self.supabase_manager:
                logger.warning("⚠️ Supabase manager غير متاح")
                return
            
            # الحصول على الإعدادات من Supabase
            supabase_settings = self.supabase_manager.get_all_settings()
            if not supabase_settings:
                logger.info("ℹ️ لا توجد إعدادات في Supabase، سيتم إنشاؤها")
                # إنشاء الإعدادات الافتراضية في Supabase
                self._create_default_settings_in_supabase()
                return
            
            # الحصول على الإعدادات المحلية
            local_settings = self.get_all_settings()
            
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # مزامنة الإعدادات من Supabase إلى المحلي
            updated_count = 0
            for key, value in supabase_settings.items():
                if key not in local_settings or local_settings[key] != value:
                    cursor.execute('''
                        INSERT OR REPLACE INTO app_settings (key, value, updated_at)
                        VALUES (?, ?, datetime('now'))
                    ''', (key, value))
                    updated_count += 1
                    logger.info(f"🔄 تم مزامنة الإعداد: {key} = {value}")
            
            # مزامنة الإعدادات المحلية إلى Supabase إذا كانت أحدث
            for key, value in local_settings.items():
                if key not in supabase_settings:
                    try:
                        self.supabase_manager.update_setting(key, value)
                        logger.info(f"🔄 تم مزامنة الإعداد المحلي إلى Supabase: {key} = {value}")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed في مزامنة الإعداد المحلي {key}: {e}")
            
            conn.commit()
            conn.close()
            
            if updated_count > 0:
                logger.info(f"✅ تم مزامنة {updated_count} إعداد من Supabase")
            else:
                logger.info("✅ الإعدادات متزامنة بالفعل")
            
        except Exception as e:
            logger.error(f"❌ Error في مزامنة الإعدادات من Supabase: {e}")
            # تسجيل تفاصيل أكثر للتصحيح
            logger.error(f"🔍 تفاصيل الخطأ: {type(e).__name__}: {str(e)}")
    
    def _create_default_settings_in_supabase(self):
        """إنشاء الإعدادات الافتراضية في Supabase"""
        try:
            if not self.supabase_manager:
                return
            
            default_settings = {
                'work_start_time': '08:00:00',
                'late_allowance_minutes': '15',
                'theme': 'light',
                'language': 'ar',
                'auto_sync': 'true',
                'sync_interval': '300'
            }
            
            for key, value in default_settings.items():
                try:
                    self.supabase_manager.update_setting(key, value)
                    logger.info(f"✅ تم إنشاء الإعداد الافتراضي في Supabase: {key} = {value}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed في إنشاء الإعداد {key}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ Error في إنشاء الإعدادات الافتراضية: {e}")
    
    def force_sync_settings_to_supabase(self):
        """مزامنة قسرية لجميع الإعدادات المحلية إلى Supabase"""
        try:
            if not self.supabase_manager:
                logger.warning("⚠️ Supabase manager غير متاح")
                return False
            
            local_settings = self.get_all_settings()
            success_count = 0
            
            for key, value in local_settings.items():
                try:
                    success = self.supabase_manager.update_setting(key, value)
                    if success:
                        success_count += 1
                        logger.info(f"✅ تم مزامنة الإعداد: {key} = {value}")
                    else:
                        logger.warning(f"⚠️ Failed في مزامنة الإعداد: {key}")
                except Exception as e:
                    logger.error(f"❌ Error في مزامنة الإعداد {key}: {e}")
            
            logger.info(f"🎯 تم مزامنة {success_count}/{len(local_settings)} إعداد بنجاح")
            return success_count == len(local_settings)
            
        except Exception as e:
            logger.error(f"❌ Error في المزامنة القسرية: {e}")
            return False
    
    def _sync_locations_from_supabase(self):
        """مزامنة المواقع من Supabase"""
        try:
            # الحصول على المواقع من Supabase
            supabase_locations = self.supabase_manager.get_all_locations()
            if not supabase_locations:
                logger.info("ℹ️ لا توجد مواقع في Supabase")
                return
            
            # الحصول على المواقع المحلية
            local_locations = {loc['id']: loc for loc in self.get_all_locations()}
            
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            for supabase_loc in supabase_locations:
                loc_id = supabase_loc.get('id')
                if not loc_id:
                    continue
                
                if loc_id in local_locations:
                    # Update الموقع الموجود
                    local_loc = local_locations[loc_id]
                    if self._has_location_changes(supabase_loc, local_loc):
                        self._update_local_location(cursor, loc_id, supabase_loc)
                        logger.info(f"🔄 تم Update الموقع: {supabase_loc.get('name')}")
                else:
                    # Add موقع جديد
                    self._add_local_location(cursor, supabase_loc)
                    logger.info(f"➕ تم Add موقع جديد: {supabase_loc.get('name')}")
            
            # Delete المواقع المحذوفة من Supabase
            supabase_ids = {loc.get('id') for loc in supabase_locations}
            for local_id in local_locations:
                if local_id not in supabase_ids:
                    self._delete_local_location(cursor, local_id)
                    logger.info(f"🗑️ تم Delete موقع محلي: {local_locations[local_id].get('name')}")
            
            conn.commit()
            conn.close()
            logger.info(f"✅ تم مزامنة {len(supabase_locations)} موقع من Supabase")
            
        except Exception as e:
            logger.error(f"❌ Error في مزامنة المواقع من Supabase: {e}")
    
    def _sync_holidays_from_supabase(self):
        """مزامنة الإجازات من Supabase"""
        try:
            # الحصول على الإجازات من Supabase
            supabase_holidays = self.supabase_manager.get_all_holidays()
            if not supabase_holidays:
                logger.info("ℹ️ لا توجد إجازات في Supabase")
                return
            
            # الحصول على الإجازات المحلية
            local_holidays = {hol['id']: hol for hol in self.get_all_holidays()}
            
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            for supabase_holiday in supabase_holidays:
                holiday_id = supabase_holiday.get('id')
                if not holiday_id:
                    continue
                
                if holiday_id in local_holidays:
                    # Update الإجازة الموجودة
                    local_holiday = local_holidays[holiday_id]
                    if self._has_holiday_changes(supabase_holiday, local_holiday):
                        self._update_local_holiday(cursor, holiday_id, supabase_holiday)
                        logger.info(f"🔄 تم Update الإجازة: {supabase_holiday.get('description')}")
                else:
                    # Add إجازة جديدة
                    self._add_local_holiday(cursor, supabase_holiday)
                    logger.info(f"➕ تم Add إجازة جديدة: {supabase_holiday.get('description')}")
            
            # Delete الإجازات المحذوفة من Supabase
            supabase_ids = {holiday.get('id') for holiday in supabase_holidays}
            for local_id in local_holidays:
                if local_id not in supabase_ids:
                    self._delete_local_holiday(cursor, local_id)
                    logger.info(f"🗑️ تم Delete إجازة محلية: {local_holidays[local_id].get('description')}")
            
            conn.commit()
            conn.close()
            logger.info(f"✅ تم مزامنة {len(supabase_holidays)} إجازة من Supabase")
            
        except Exception as e:
            logger.error(f"❌ Error في مزامنة الإجازات من Supabase: {e}")
    
    def _has_employee_changes(self, supabase_emp: Dict, local_emp: Dict) -> bool:
        """فحص ما إذا كان الموظف قد تغير في Supabase"""
        fields_to_check = ['name', 'employee_code', 'job_title', 'department', 'phone_number', 'qr_code']
        for field in fields_to_check:
            if supabase_emp.get(field) != local_emp.get(field):
                return True
        return False
    
    def _has_user_changes(self, supabase_user: Dict, local_user: Dict) -> bool:
        """فحص ما إذا كان المستخدم قد تغير في Supabase"""
        fields_to_check = ['username', 'role']
        for field in fields_to_check:
            if supabase_user.get(field) != local_user.get(field):
                return True
        return False
    
    def _has_attendance_changes(self, supabase_record: Dict, local_record: Dict) -> bool:
        """فحص ما إذا كان سجل الحضور قد تغير في Supabase"""
        fields_to_check = ['check_time', 'date', 'type', 'notes']
        for field in fields_to_check:
            if supabase_record.get(field) != local_record.get(field):
                return True
        return False
    
    def _has_location_changes(self, supabase_loc: Dict, local_loc: Dict) -> bool:
        """فحص ما إذا كان الموقع قد تغير في Supabase"""
        fields_to_check = ['name', 'latitude', 'longitude', 'radius_meters']
        for field in fields_to_check:
            if supabase_loc.get(field) != local_loc.get(field):
                return True
        return False
    
    def _has_holiday_changes(self, supabase_holiday: Dict, local_holiday: Dict) -> bool:
        """فحص ما إذا كان الإجازة قد تغير في Supabase"""
        fields_to_check = ['description', 'date']
        for field in fields_to_check:
            if supabase_holiday.get(field) != local_holiday.get(field):
                return True
        return False
    
    def _update_local_employee(self, cursor, emp_id: int, supabase_data: Dict):
        """Update employee محلي ببيانات Supabase"""
        cursor.execute('''
            UPDATE employees 
            SET name = ?, employee_code = ?, job_title = ?, department = ?, 
                phone_number = ?, qr_code = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (
            supabase_data.get('name', ''),
            supabase_data.get('employee_code', ''),
            supabase_data.get('job_title', ''),
            supabase_data.get('department', ''),
            supabase_data.get('phone_number', ''),
            supabase_data.get('qr_code', ''),
            emp_id
        ))
    
    def _add_local_employee(self, cursor, supabase_data: Dict):
        """Add موظف محلي من بيانات Supabase"""
        cursor.execute('''
            INSERT INTO employees (id, name, employee_code, job_title, department, phone_number, web_fingerprint, device_token, qr_code)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            supabase_data.get('id'),
            supabase_data.get('name', ''),
            supabase_data.get('employee_code', ''),
            supabase_data.get('job_title', ''),
            supabase_data.get('department', ''),
            supabase_data.get('phone_number', ''),
            supabase_data.get('web_fingerprint', ''),
            supabase_data.get('device_token', ''),
            supabase_data.get('qr_code', '')
        ))
    
    def _delete_local_employee(self, cursor, emp_id: int):
        """Delete موظف محلي"""
        cursor.execute('DELETE FROM employees WHERE id = ?', (emp_id,))
    
    def _update_local_user(self, cursor, user_id: int, supabase_data: Dict):
        """Update مستخدم محلي ببيانات Supabase"""
        cursor.execute('''
            UPDATE users 
            SET username = ?, role = ?
            WHERE id = ?
        ''', (
            supabase_data.get('username', ''),
            supabase_data.get('role', 'Viewer'),
            user_id
        ))
    
    def _add_local_user(self, cursor, supabase_data: Dict):
        """Add مستخدم محلي من بيانات Supabase"""
        cursor.execute('''
            INSERT INTO users (id, username, password, role)
            VALUES (?, ?, ?, ?)
        ''', (
            supabase_data.get('id'),
            supabase_data.get('username', ''),
            supabase_data.get('password', ''),
            supabase_data.get('role', 'Viewer')
        ))
    
    def _delete_local_user(self, cursor, user_id: int):
        """Delete مستخدم محلي"""
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    
    def _get_local_attendance_dict(self) -> Dict:
        """الحصول على سجلات الحضور المحلية كقاموس"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, employee_id, check_time, date, type, notes, location_id
                FROM attendance
            ''')
            
            records = {}
            for row in cursor.fetchall():
                records[row[0]] = {
                    'id': row[0],
                    'employee_id': row[1],
                    'check_time': row[2],
                    'date': row[3],
                    'type': row[4],
                    'notes': row[5],
                    'location_id': row[6]
                }
            
            conn.close()
            return records
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على سجلات الحضور المحلية: {e}")
            return {}
    
    def _update_local_attendance(self, cursor, record_id: int, supabase_data: Dict):
        """Update سجل حضور محلي ببيانات Supabase"""
        cursor.execute('''
            UPDATE attendance 
            SET employee_id = ?, check_time = ?, date = ?, type = ?, notes = ?, location_id = ?
            WHERE id = ?
        ''', (
            supabase_data.get('employee_id'),
            supabase_data.get('check_time'),
            supabase_data.get('date'),
            supabase_data.get('type', 'Check-In'),
            supabase_data.get('notes', ''),
            supabase_data.get('location_id'),
            record_id
        ))
    
    def _add_local_attendance(self, cursor, supabase_data: Dict):
        """Add سجل حضور محلي من بيانات Supabase"""
        cursor.execute('''
            INSERT INTO attendance (id, employee_id, check_time, date, type, notes, location_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            supabase_data.get('id'),
            supabase_data.get('employee_id'),
            supabase_data.get('check_time'),
            supabase_data.get('date'),
            supabase_data.get('type', 'Check-In'),
            supabase_data.get('notes', ''),
            supabase_data.get('location_id')
        ))
    
    def _delete_local_attendance(self, cursor, record_id: int):
        """Delete سجل حضور محلي"""
        cursor.execute('DELETE FROM attendance WHERE id = ?', (record_id,))
    
    def _update_local_location(self, cursor, loc_id: int, supabase_data: Dict):
        """Update موقع محلي ببيانات Supabase"""
        cursor.execute('''
            UPDATE locations 
            SET name = ?, latitude = ?, longitude = ?, radius_meters = ?
            WHERE id = ?
        ''', (
            supabase_data.get('name', ''),
            supabase_data.get('latitude', 0.0),
            supabase_data.get('longitude', 0.0),
            supabase_data.get('radius_meters', 100),
            loc_id
        ))
    
    def _add_local_location(self, cursor, supabase_data: Dict):
        """Add موقع محلي من بيانات Supabase"""
        cursor.execute('''
            INSERT INTO locations (name, latitude, longitude, radius_meters)
            VALUES (?, ?, ?, ?)
        ''', (
            supabase_data.get('name', ''),
            supabase_data.get('latitude', 0.0),
            supabase_data.get('longitude', 0.0),
            supabase_data.get('radius_meters', 100)
        ))
    
    def _delete_local_location(self, cursor, loc_id: int):
        """Delete موقع محلي"""
        cursor.execute('DELETE FROM locations WHERE id = ?', (loc_id,))
    
    def _update_local_holiday(self, cursor, holiday_id: int, supabase_data: Dict):
        """Update إجازة محلية ببيانات Supabase"""
        cursor.execute('''
            UPDATE holidays 
            SET description = ?, date = ?
            WHERE id = ?
        ''', (
            supabase_data.get('description', ''),
            supabase_data.get('date', ''),
            holiday_id
        ))
    
    def _add_local_holiday(self, cursor, supabase_data: Dict):
        """Add إجازة محلية من بيانات Supabase"""
        cursor.execute('''
            INSERT INTO holidays (description, date)
            VALUES (?, ?)
        ''', (
            supabase_data.get('description', ''),
            supabase_data.get('date', '')
        ))
    
    def _delete_local_holiday(self, cursor, holiday_id: int):
        """Delete إجازة محلية"""
        cursor.execute('DELETE FROM holidays WHERE id = ?', (holiday_id,))
    
    # === دوال إدارة الموظفين ===
    
    def get_all_employees(self) -> List[Dict]:
        """الحصول على جميع الموظفين"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, employee_code, name, job_title, department, phone_number, web_fingerprint, device_token, qr_code
                FROM employees
                ORDER BY name
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            employees = []
            for row in rows:
                employees.append({
                    'id': row[0],
                    'employee_code': row[1],
                    'name': row[2],
                    'job_title': row[3] or '',
                    'department': row[4] or '',
                    'phone_number': row[5] or '',
                    'web_fingerprint': row[6] or '',
                    'device_token': row[7] or '',
                    'qr_code': row[8] or ''
                })
            
            return employees
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على الموظفين: {e}")
            return []
    
    def _get_attendance_status(self, date: str, type: str) -> str:
        """الحصول على حالة الحضور"""
        try:
            if not date:
                return 'No Attendance'
            
            from datetime import datetime
            attendance_date = datetime.strptime(date, '%Y-%m-%d').date()
            today = datetime.now().date()
            
            if attendance_date == today:
                if type == 'Check-In':
                    return 'Present Today'
                elif type == 'Check-Out':
                    return 'Left Today'
                else:
                    return 'Present Today'
            elif attendance_date < today:
                return f'Last: {date}'
            else:
                return 'Future Date'
                
        except Exception:
            return 'Unknown'
    
    def get_employees_with_attendance(self) -> List[Dict]:
        """الحصول على الموظفين مع حالة الحضور"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT e.id, e.employee_code, e.name, e.job_title, e.department, e.phone_number, e.qr_code,
                       a.check_time, a.date, a.type, a.notes
                FROM employees e
                LEFT JOIN (
                    SELECT employee_id, check_time, date, type, notes,
                           ROW_NUMBER() OVER (PARTITION BY employee_id ORDER BY date DESC, check_time DESC) as rn
                    FROM attendance
                ) a ON e.id = a.employee_id AND a.rn = 1
                ORDER BY e.name
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            employees = []
            for row in rows:
                employee = {
                    'id': row[0],
                    'employee_code': row[1],
                    'name': row[2],
                    'job_title': row[3] or '',
                    'department': row[4] or '',
                    'phone_number': row[5] or '',
                    'qr_code': row[6] or '',
                    'last_attendance': {
                        'check_time': row[7],
                        'date': row[8],
                        'type': row[9],
                        'notes': row[10] or ''
                    } if row[7] else None
                }
                employees.append(employee)
            
            return employees
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على الموظفين مع الحضور: {e}")
            return []
    
    def add_employee(self, data: Dict) -> Optional[int]:
        """Add موظف مع مزامنة فورية محسنة"""
        try:
            # العملية المحلية بدون قفل طويل
            conn = sqlite3.connect(self.local_db_path, timeout=1.0)
            cursor = conn.cursor()
            
            # فحص القيود الفريدة قبل الAdd
            if data.get('employee_code'):
                cursor.execute('SELECT id FROM employees WHERE employee_code = ?', (data['employee_code'],))
                if cursor.fetchone():
                    conn.close()
                    raise ValueError(f"كود الموظف '{data['employee_code']}' مستخدم بالفعل")
            
            if data.get('phone_number'):
                cursor.execute('SELECT id FROM employees WHERE phone_number = ?', (data['phone_number'],))
                if cursor.fetchone():
                    conn.close()
                    raise ValueError(f"رقم الهاتف '{data['phone_number']}' مستخدم بالفعل")
            
            cursor.execute('''
                INSERT INTO employees (employee_code, name, job_title, department, phone_number, web_fingerprint, device_token, qr_code)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                data['employee_code'], 
                data['name'], 
                data.get('job_title', ''),
                data.get('department', ''),
                data.get('phone_number', ''),
                data.get('web_fingerprint', ''),
                data.get('device_token', ''),
                data.get('qr_code', '')
            ))
            
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"✅ تم Add موظف: {data['name']}")
            
            # مزامنة فورية في الخلفية (بدون انتظار)
            self._immediate_sync("employees", record_id, "INSERT", data)
            
            # Add إلى قائمة المزامنة (بدون انتظار)
            self._add_to_sync_queue("employees", record_id, "INSERT", data)
            
            return record_id
            
        except ValueError as e:
            # Error في القيود الفريدة
            logger.warning(f"⚠️ {e}")
            raise e
        except Exception as e:
            logger.error(f"❌ Error في Add موظف: {e}")
            return None
    
    def update_employee(self, employee_id: int, update_data: Dict) -> bool:
        """Update employee مع مزامنة فورية"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # فحص القيود الفريدة قبل الUpdate
            if 'employee_code' in update_data:
                cursor.execute('SELECT id FROM employees WHERE employee_code = ? AND id != ?', 
                             (update_data['employee_code'], employee_id))
                if cursor.fetchone():
                    conn.close()
                    raise ValueError(f"كود الموظف '{update_data['employee_code']}' مستخدم بالفعل")
            
            if 'phone_number' in update_data:
                cursor.execute('SELECT id FROM employees WHERE phone_number = ? AND id != ?', 
                             (update_data['phone_number'], employee_id))
                if cursor.fetchone():
                    conn.close()
                    raise ValueError(f"رقم الهاتف '{update_data['phone_number']}' مستخدم بالفعل")
            
            # بناء استعلام الUpdate ديناميكياً
            update_fields = []
            params = []
            
            for field, value in update_data.items():
                if field in ['employee_code', 'name', 'job_title', 'department', 'phone_number', 'qr_code']:
                    update_fields.append(f"{field} = ?")
                    params.append(value)
            
            if not update_fields:
                logger.warning("⚠️ لا توجد حقول صالحة للUpdate")
                return False
            
            # Add updated_at كمعامل منفصل
            update_fields.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            
            # Add employee_id في النهاية
            params.append(employee_id)
            
            query = f'''
                UPDATE employees 
                SET {', '.join(update_fields)}
                WHERE id = ?
            '''
            
            cursor.execute(query, params)
            
            conn.commit()
            conn.close()
            
            # Add إلى قائمة انتظار المزامنة
            self._add_to_sync_queue("employees", employee_id, "UPDATE", update_data)
            
            # مزامنة فورية
            self._immediate_sync("employees", employee_id, "UPDATE", update_data)
            
            logger.info(f"✅ تم Update employee: ID {employee_id}")
            return True
            
        except ValueError as e:
            # Error في القيود الفريدة
            logger.warning(f"⚠️ {e}")
            raise e
        except Exception as e:
            logger.error(f"❌ Error في Update employee: {e}")
            return False
    
    def delete_employee(self, employee_id: int) -> bool:
        """Delete موظف مع مزامنة فورية"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM employees WHERE id = ?', (employee_id,))
            
            # Add إلى قائمة انتظار المزامنة
            self._add_to_sync_queue("employees", employee_id, "DELETE", {'id': employee_id})
            
            # مزامنة فورية
            self._immediate_sync("employees", employee_id, "DELETE", {'id': employee_id})
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ تم Delete موظف: ID {employee_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error في Delete موظف: {e}")
            return False
    
    def update_employee_device_info(self, employee_id: int, fingerprint: str, token: str) -> bool:
        """Update معلومات جهاز الموظف مع مزامنة فورية"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE employees 
                SET web_fingerprint = ?, device_token = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (fingerprint, token, employee_id))
            
            conn.commit()
            conn.close()
            
            # Add إلى قائمة انتظار المزامنة
            self._add_to_sync_queue("employees", employee_id, "UPDATE", {
                'web_fingerprint': fingerprint,
                'device_token': token
            })
            
            # مزامنة فورية
            self._immediate_sync("employees", employee_id, "UPDATE", {
                'web_fingerprint': fingerprint,
                'device_token': token
            })
            
            logger.info(f"✅ تم Update معلومات جهاز الموظف: ID {employee_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error في Update معلومات جهاز الموظف: {e}")
            return False
    
    def reset_employee_device_info(self, employee_id: int) -> bool:
        """إعادة تعيين معلومات جهاز الموظف مع مزامنة فورية"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE employees 
                SET web_fingerprint = NULL, device_token = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (employee_id,))
            
            conn.commit()
            conn.close()
            
            # Add إلى قائمة انتظار المزامنة
            self._add_to_sync_queue("employees", employee_id, "UPDATE", {
                'web_fingerprint': None,
                'device_token': None
            })
            
            # مزامنة فورية
            self._immediate_sync("employees", employee_id, "UPDATE", {
                'web_fingerprint': None,
                'device_token': None
            })
            
            logger.info(f"✅ تم إعادة تعيين معلومات جهاز الموظف: ID {employee_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error في إعادة تعيين معلومات جهاز الموظف: {e}")
            return False
    
    # === دوال إدارة المستخدمين ===
    
    def add_user(self, user_data: Dict) -> Optional[int]:
        """Add مستخدم مع مزامنة فورية"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # فحص القيود الفريدة قبل الAdd
            if user_data.get('username'):
                cursor.execute('SELECT id FROM users WHERE username = ?', (user_data['username'],))
                if cursor.fetchone():
                    conn.close()
                    raise ValueError(f"اسم المستخدم '{user_data['username']}' مستخدم بالفعل")
            
            cursor.execute('''
                INSERT INTO users (username, password, role)
                VALUES (?, ?, ?)
            ''', (user_data['username'], user_data['password'], user_data['role']))
            
            record_id = cursor.lastrowid
            
            # Add إلى قائمة انتظار المزامنة
            self._add_to_sync_queue("users", record_id, "INSERT", user_data)
            
            # مزامنة فورية
            self._immediate_sync("users", record_id, "INSERT", user_data)
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ تم Add مستخدم: {user_data['username']}")
            return record_id
            
        except ValueError as e:
            # Error في القيود الفريدة
            logger.warning(f"⚠️ {e}")
            raise e
        except Exception as e:
            logger.error(f"❌ Error في Add مستخدم: {e}")
            return None
    
    def update_user(self, user_id: int, update_data: Dict) -> bool:
        """Update مستخدم مع مزامنة فورية"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # فحص القيود الفريدة قبل الUpdate
            if 'username' in update_data:
                cursor.execute('SELECT id FROM users WHERE username = ? AND id != ?', 
                             (update_data['username'], user_id))
                if cursor.fetchone():
                    conn.close()
                    raise ValueError(f"اسم المستخدم '{update_data['username']}' مستخدم بالفعل")
            
            # بناء استعلام الUpdate ديناميكياً
            update_fields = []
            params = []
            
            for field, value in update_data.items():
                if field in ['username', 'password', 'role']:
                    update_fields.append(f"{field} = ?")
                    params.append(value)
            
            if not update_fields:
                logger.warning("⚠️ لا توجد حقول صالحة لUpdate المستخدم")
                return False
            
            # Add user_id في النهاية
            params.append(user_id)
            
            query = f'''
                UPDATE users 
                SET {', '.join(update_fields)}
                WHERE id = ?
            '''
            
            cursor.execute(query, params)
            
            conn.commit()
            conn.close()
            
            # Add إلى قائمة انتظار المزامنة
            self._add_to_sync_queue("users", user_id, "UPDATE", update_data)
            
            # مزامنة فورية
            self._immediate_sync("users", user_id, "UPDATE", update_data)
            
            logger.info(f"✅ تم Update مستخدم: ID {user_id}")
            return True
            
        except ValueError as e:
            # Error في القيود الفريدة
            logger.warning(f"⚠️ {e}")
            raise e
        except Exception as e:
            logger.error(f"❌ Error في Update مستخدم: {e}")
            return False
    
    def delete_user(self, user_id: int) -> bool:
        """Delete مستخدم مع مزامنة فورية"""
        try:
            # لا يمكن Delete المستخدم الرئيسي (ID = 1)
            if user_id == 1:
                logger.warning("⚠️ لا يمكن Delete المستخدم الرئيسي")
                return False
            
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # التحقق من وجود المستخدم
            cursor.execute('SELECT username FROM users WHERE id = ?', (user_id,))
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"⚠️ المستخدم غير موجود: ID {user_id}")
                return False
            
            username = result[0]
            
            # Delete المستخدم
            cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
            
            # Add إلى قائمة انتظار المزامنة
            self._add_to_sync_queue("users", user_id, "DELETE", {'username': username})
            
            # مزامنة فورية
            self._immediate_sync("users", user_id, "DELETE", {'username': username})
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ تم Delete مستخدم: {username} (ID: {user_id})")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error في Delete مستخدم: {e}")
            return False
    
    def record_attendance(self, attendance_data: Dict) -> Optional[int]:
        """تسجيل حضور مع مزامنة فورية - يدعم البيانات كقاموس أو معاملات منفصلة"""
        try:
            # دعم النداء بالطريقتين
            if isinstance(attendance_data, dict):
                employee_id = attendance_data.get('employee_id')
                attendance_type = attendance_data.get('type')
                location_id = attendance_data.get('location_id')
                notes = attendance_data.get('notes', '')
                provided_time = attendance_data.get('check_time')
                provided_date = attendance_data.get('date')
            else:
                # للتوافق مع النداء القديم - هذا لا يحدث عادة
                raise ValueError("البيانات يجب أن تكون dictionary")
            
            conn = sqlite3.connect(self.local_db_path, timeout=1.0)
            cursor = conn.cursor()
            
            # استخدام الوقت المحدد أو الحالي
            if provided_time:
                current_time = provided_time
            else:
                current_time = datetime.now().strftime('%H:%M:%S')
            
            if provided_date:
                current_date = provided_date
            else:
                current_date = datetime.now().strftime('%Y-%m-%d')
            
            # إدخال في قاعدة البيانات المحلية
            cursor.execute('''
                INSERT INTO attendance (employee_id, check_time, date, type, notes, location_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (employee_id, current_time, current_date, attendance_type, notes, location_id))
            
            record_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # إعداد البيانات للمزامنة
            sync_data = {
                'employee_id': employee_id,
                'check_time': current_time,
                'date': current_date,
                'type': attendance_type,
                'notes': notes,
                'location_id': location_id
            }
            
            logger.info(f"✅ تم تسجيل حضور محلياً: Employee ID {employee_id}")
            
            # مزامنة فورية في الخلفية
            self._immediate_sync("attendance", record_id, "INSERT", sync_data)
            
            # Add إلى قائمة انتظار المزامنة
            self._add_to_sync_queue("attendance", record_id, "INSERT", sync_data)
            
            return record_id
            
        except Exception as e:
            logger.error(f"❌ Error في تسجيل حضور: {e}")
            return None
    
    # === دوال إدارة الإعدادات ===
    
    def get_all_settings(self) -> Dict:
        """الحصول على جميع الإعدادات من قاعدة البيانات المحلية - محدث"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT key, value FROM app_settings')
            rows = cursor.fetchall()
            conn.close()
            
            settings = {}
            for row in rows:
                settings[row[0]] = row[1]
            
            # Add إعدادات افتراضية إذا لم توجد
            if not settings:
                default_settings = {
                    'theme': 'light',
                    'language': 'ar',
                    'auto_backup': 'true',
                    'sync_interval': '30'
                }
                
                conn = sqlite3.connect(self.local_db_path)
                cursor = conn.cursor()
                
                for key, value in default_settings.items():
                    cursor.execute('''
                        INSERT OR REPLACE INTO app_settings (key, value)
                        VALUES (?, ?)
                    ''', (key, value))
                
                conn.commit()
                conn.close()
                
                return default_settings
            
            return settings
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على الإعدادات: {e}")
            return {'theme': 'light', 'language': 'ar'}
    
    def get_setting(self, key: str, default_value: str = '') -> str:
        """الحصول على إعداد من قاعدة البيانات المحلية"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT value FROM app_settings WHERE key = ?', (key,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return result[0]
            else:
                return default_value
                
        except Exception as e:
            logger.error(f"❌ Error في الحصول على الإعداد {key}: {e}")
            return default_value or ''
    
    def save_setting(self, key: str, value: str) -> bool:
        """Save إعداد مع مزامنة فورية - محسن"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # التحقق من القيمة الحالية
            cursor.execute('SELECT value FROM app_settings WHERE key = ?', (key,))
            current_result = cursor.fetchone()
            current_value = current_result[0] if current_result else None
            
            # Save الإعداد الجديد
            cursor.execute('''
                INSERT OR REPLACE INTO app_settings (key, value, updated_at)
                VALUES (?, ?, datetime('now'))
            ''', (key, value))
            
            conn.commit()
            conn.close()
            
            # تسجيل التغيير
            if current_value != value:
                logger.info(f"✅ تم تغيير الإعداد: {key} = {current_value} → {value}")
                
                # مزامنة فورية مع Supabase إذا كان متاحاً
                try:
                    if self.supabase_manager:
                        # Update الإعداد في Supabase
                        success = self.supabase_manager.update_setting(key, value)
                        if success:
                            logger.info(f"🔄 تم مزامنة الإعداد {key} مع Supabase بنجاح")
                            # تحديث hash البيانات للتغيير
                            self.change_detection['has_changes'] = True
                        else:
                            logger.warning(f"⚠️ Failed في مزامنة الإعداد {key} مع Supabase")
                    else:
                        logger.warning(f"⚠️ Supabase manager غير متاح للمزامنة")
                except Exception as e:
                    logger.error(f"❌ Error في مزامنة الإعداد {key} مع Supabase: {e}")
                    # إضافة الإعداد إلى قائمة انتظار المزامنة
                    self._add_to_sync_queue('app_settings', key, 'update', {'key': key, 'value': value})
            else:
                logger.info(f"✅ تم Save الإعداد: {key} = {value}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error في Save الإعداد: {e}")
            return False
    
    # === دوال للتوافق مع باقي النظام ===
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """الحصول على مستخدم بواسطة المعرف"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, password, role
                FROM users WHERE id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'username': result[1],
                    'password': result[2],
                    'role': result[3],
                    'created_at': None,  # غير متوفر في قاعدة البيانات المحلية
                    'updated_at': None   # غير متوفر في قاعدة البيانات المحلية
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على المستخدم: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """الحصول على مستخدم بواسطة اسم المستخدم"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, password, role
                FROM users WHERE username = ?
            ''', (username,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'username': result[1],
                    'password': result[2],
                    'role': result[3],
                    'created_at': None,  # غير متوفر في قاعدة البيانات المحلية
                    'updated_at': None   # غير متوفر في قاعدة البيانات المحلية
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على المستخدم: {e}")
            return None
    
    def update_user_password(self, user_id: int, new_password: str) -> bool:
        """Update كلمة مرور المستخدم"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET password = ? WHERE id = ?
            ''', (new_password, user_id))
            
            conn.commit()
            conn.close()
            
            # Add إلى قائمة انتظار المزامنة
            self._add_to_sync_queue("users", user_id, "UPDATE", {'password': new_password})
            
            # مزامنة فورية
            self._immediate_sync("users", user_id, "UPDATE", {'password': new_password})
            
            logger.info(f"✅ تم Update كلمة مرور المستخدم: ID {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error في Update كلمة مرور المستخدم: {e}")
            return False
    
    def update_user_role(self, user_id: int, new_role: str) -> bool:
        """Update دور المستخدم"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE users SET role = ? WHERE id = ?
            ''', (new_role, user_id))
            
            conn.commit()
            conn.close()
            
            # Add إلى قائمة انتظار المزامنة
            self._add_to_sync_queue("users", user_id, "UPDATE", {'role': new_role})
            
            # مزامنة فورية
            self._immediate_sync("users", user_id, "UPDATE", {'role': new_role})
            
            logger.info(f"✅ تم Update دور المستخدم: ID {user_id} إلى {new_role}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error في Update دور المستخدم: {e}")
            return False
    
    def search_users(self, search_term: str) -> List[Dict]:
        """الSearch عن المستخدمين"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, password, role
                FROM users 
                WHERE username LIKE ? OR role LIKE ?
            ''', (f'%{search_term}%', f'%{search_term}%'))
            
            results = cursor.fetchall()
            conn.close()
            
            users = []
            for result in results:
                users.append({
                    'id': result[0],
                    'username': result[1],
                    'password': result[2],
                    'role': result[3],
                    'created_at': None,
                    'updated_at': None
                })
            
            return users
            
        except Exception as e:
            logger.error(f"❌ Error في الSearch عن المستخدمين: {e}")
            return []
    
    def verify_user_password(self, username: str, password: str) -> bool:
        """التحقق من صحة كلمة مرور المستخدم"""
        try:
            user = self.get_user_by_username(username)
            if user and user['password'] == password:
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ Error في التحقق من كلمة المرور: {e}")
            return False
    
    def get_employee_by_id(self, employee_id: int) -> Optional[Dict]:
        """الحصول على موظف بواسطة المعرف"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, employee_code, name, job_title, department, phone_number, web_fingerprint, device_token, qr_code
                FROM employees WHERE id = ?
            ''', (employee_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'employee_code': result[1],
                    'name': result[2],
                    'job_title': result[3] or '',
                    'department': result[4] or '',
                    'phone_number': result[5] or '',
                    'web_fingerprint': result[6] or '',
                    'device_token': result[7] or '',
                    'qr_code': result[8] or ''
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على الموظف: {e}")
            return None
    
    def get_employee_by_username(self, username: str) -> Optional[Dict]:
        """الحصول على موظف بواسطة اسم المستخدم"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, employee_code, name, job_title, department, phone_number, qr_code
                FROM employees WHERE name = ?
            ''', (username,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'employee_code': result[1],
                    'name': result[2],
                    'job_title': result[3] or '',
                    'department': result[4] or '',
                    'phone_number': result[5] or '',
                    'qr_code': result[6] or ''
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على الموظف: {e}")
            return None
    
    def get_employee_by_code(self, employee_code: str) -> Optional[Dict]:
        """الحصول على موظف بواسطة كود الموظف"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, employee_code, name, job_title, department, phone_number, web_fingerprint, device_token, qr_code
                FROM employees WHERE employee_code = ?
            ''', (employee_code,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'employee_code': result[1],
                    'name': result[2],
                    'job_title': result[3] or '',
                    'department': result[4] or '',
                    'phone_number': result[5] or '',
                    'web_fingerprint': result[6] or '',
                    'device_token': result[7] or '',
                    'qr_code': result[8] or ''
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على الموظف: {e}")
            return None
    
    def get_all_users(self) -> List[Dict]:
        """الحصول على جميع المستخدمين"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, username, password, role
                FROM users
                ORDER BY username
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            users = []
            for row in rows:
                users.append({
                    'id': row[0],
                    'username': row[1],
                    'password': row[2],
                    'role': row[3]
                })
            
            return users
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على المستخدمين: {e}")
            return []
    
    def get_all_locations(self) -> List[Dict]:
        """الحصول على جميع المواقع"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT id, name, latitude, longitude, radius_meters FROM locations')
            locations = []
            
            for row in cursor.fetchall():
                location = {
                    'id': row[0],
                    'name': row[1],
                    'latitude': row[2] or 0.0,
                    'longitude': row[3] or 0.0,
                    'radius_meters': row[4] or 100,
                    'description': ''  # Add حقل فارغ للتوافق مع UI
                }
                locations.append(location)
            
            conn.close()
            return locations
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على المواقع: {e}")
            return []
    
    def get_all_holidays(self) -> List[Dict]:
        """الحصول على جميع الإجازات"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, description, date
                FROM holidays
                ORDER BY date
            ''')
            
            rows = cursor.fetchall()
            conn.close()
            
            holidays = []
            for row in rows:
                holidays.append({
                    'id': row[0],
                    'description': row[1],  # Use description directly
                    'date': row[2],
                    'type': 'national'  # Default type since it's not in the schema
                })
            
            return holidays
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على الإجازات: {e}")
            return []
    
    def _location_name_exists(self, name: str) -> bool:
        """التحقق من وجود اسم موقع مشابه"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM locations WHERE name = ?', (name,))
            count = cursor.fetchone()[0]
            
            conn.close()
            return count > 0
            
        except Exception as e:
            logger.error(f"❌ Error في التحقق من اسم الموقع: {e}")
            return False
    
    def _location_name_exists_except_current(self, name: str, current_id: int) -> bool:
        """التحقق من وجود اسم موقع مشابه (باستثناء الموقع الحالي)"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM locations WHERE name = ? AND id != ?', (name, current_id))
            count = cursor.fetchone()[0]
            
            conn.close()
            return count > 0
            
        except Exception as e:
            logger.error(f"❌ Error في التحقق من اسم الموقع: {e}")
            return False
    
    def add_location(self, data: Dict) -> Optional[int]:
        """Add موقع جديد مع مزامنة فورية"""
        try:
            # التحقق من وجود اسم مشابه
            if self._location_name_exists(data['name']):
                logger.warning(f"⚠️ اسم الموقع موجود بالفعل: {data['name']}")
                return None
            
            # استخدام timeout أطول لتجنب القفل
            conn = sqlite3.connect(self.local_db_path, timeout=20.0)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO locations (name, latitude, longitude, radius_meters)
                VALUES (?, ?, ?, ?)
            ''', (data['name'], data.get('latitude', 0.0), data.get('longitude', 0.0), data.get('radius_meters', 100)))
            
            location_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Add إلى قائمة انتظار المزامنة
            self._add_to_sync_queue("locations", location_id, "INSERT", data)
            
            # مزامنة فورية
            self._immediate_sync("locations", location_id, "INSERT", data)
            
            logger.info(f"✅ تم Add موقع: {data['name']}")
            return location_id
            
        except Exception as e:
            logger.error(f"❌ Error في Add موقع: {e}")
            return None
    
    def update_location(self, data: Dict) -> bool:
        """Update موقع مع مزامنة فورية"""
        try:
            # التحقق من وجود اسم مشابه (باستثناء الموقع الحالي)
            if self._location_name_exists_except_current(data['name'], data['id']):
                logger.warning(f"⚠️ اسم الموقع موجود بالفعل: {data['name']}")
                return False
            
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE locations 
                SET name = ?, latitude = ?, longitude = ?, radius_meters = ?
                WHERE id = ?
            ''', (data['name'], data.get('latitude', 0.0), data.get('longitude', 0.0), data.get('radius_meters', 100), data['id']))
            
            conn.commit()
            conn.close()
            
            # Add إلى قائمة انتظار المزامنة
            self._add_to_sync_queue("locations", data['id'], "UPDATE", data)
            
            # مزامنة فورية
            self._immediate_sync("locations", data['id'], "UPDATE", data)
            
            logger.info(f"✅ تم Update موقع: {data['name']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error في Update موقع: {e}")
            return False
    
    def delete_location(self, location_id: int) -> bool:
        """Delete موقع مع مزامنة فورية"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # التحقق من وجود الموقع
            cursor.execute('SELECT name FROM locations WHERE id = ?', (location_id,))
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"⚠️ الموقع غير موجود: ID {location_id}")
                return False
            
            location_name = result[0]
            
            # Delete الموقع
            cursor.execute('DELETE FROM locations WHERE id = ?', (location_id,))
            
            # Add إلى قائمة انتظار المزامنة
            self._add_to_sync_queue("locations", location_id, "DELETE", {'name': location_name})
            
            # مزامنة فورية
            self._immediate_sync("locations", location_id, "DELETE", {'name': location_name})
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ تم Delete موقع: {location_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error في Delete موقع: {e}")
            return False
    
    def add_holiday(self, date_str: str, description: str) -> Optional[int]:
        """Add إجازة جديدة مع مزامنة فورية"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # فحص وجود إجازة بنفس التاريخ
            cursor.execute('SELECT id FROM holidays WHERE date = ?', (date_str,))
            existing_holiday = cursor.fetchone()
            
            if existing_holiday:
                logger.warning(f"⚠️ إجازة بتاريخ {date_str} موجودة بالفعل")
                return existing_holiday[0]  # إرجاع ID الإجازة الموجودة
            
            cursor.execute('''
                INSERT INTO holidays (description, date)
                VALUES (?, ?)
            ''', (description, date_str))
            
            holiday_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Add إلى قائمة انتظار المزامنة
            self._add_to_sync_queue("holidays", holiday_id, "INSERT", {'description': description, 'date': date_str})
            
            # مزامنة فورية
            self._immediate_sync("holidays", holiday_id, "INSERT", {'description': description, 'date': date_str})
            
            logger.info(f"✅ تم Add إجازة: {description} - {date_str}")
            return holiday_id
            
        except Exception as e:
            logger.error(f"❌ Error في Add إجازة: {e}")
            return None
    
    def delete_holiday(self, holiday_id: int) -> bool:
        """Delete إجازة مع مزامنة فورية"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # التحقق من وجود الإجازة
            cursor.execute('SELECT description, date FROM holidays WHERE id = ?', (holiday_id,))
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"⚠️ الإجازة غير موجودة: ID {holiday_id}")
                return False
            
            holiday_name, holiday_date = result[0], result[1]
            
            # Delete الإجازة
            cursor.execute('DELETE FROM holidays WHERE id = ?', (holiday_id,))
            
            # Add إلى قائمة انتظار المزامنة
            self._add_to_sync_queue("holidays", holiday_id, "DELETE", {'description': holiday_name, 'date': holiday_date})
            
            # مزامنة فورية
            self._immediate_sync("holidays", holiday_id, "DELETE", {'description': holiday_name, 'date': holiday_date})
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ تم Delete إجازة: {holiday_name} - {holiday_date}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error في Delete إجازة: {e}")
            return False
    
    def update_setting(self, key: str, value: Any) -> bool:
        """Update إعداد مع مزامنة فورية"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO app_settings (key, value)
                VALUES (?, ?)
            ''', (key, str(value)))
            
            conn.commit()
            conn.close()
            
            # Add إلى قائمة انتظار المزامنة
            self._add_to_sync_queue("app_settings", 0, "UPDATE", {key: value})
            
            # مزامنة فورية
            self._immediate_sync("app_settings", 0, "UPDATE", {key: value})
            
            logger.info(f"✅ تم Update الإعداد: {key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error في Update الإعداد: {e}")
            return False
    
    def add_attendance_record(self, data: Dict) -> Optional[int]:
        """Add سجل حضور"""
        return self.record_attendance(data)
    
    def get_last_action_today(self, employee_id: int, date_str: str) -> Optional[str]:
        """الحصول على آخر إجراء للموظف في اليوم"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT type FROM attendance 
                WHERE employee_id = ? AND date = ?
                ORDER BY check_time DESC 
                LIMIT 1
            ''', (employee_id, date_str))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على آخر إجراء: {e}")
            return None
    
    def get_check_in_time_today(self, employee_id: int, date_str: str) -> Optional[str]:
        """الحصول على وقت تسجيل الحضور للموظف في اليوم"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT check_time FROM attendance 
                WHERE employee_id = ? AND date = ? AND type = 'Check-In'
                ORDER BY check_time ASC 
                LIMIT 1
            ''', (employee_id, date_str))
            
            result = cursor.fetchone()
            conn.close()
            
            return result[0] if result else None
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على وقت تسجيل الحضور: {e}")
            return None
    
    def update_checkout_with_duration(self, record_id: int, duration_hours: float) -> bool:
        """Update سجل تسجيل الخروج بمدة العمل"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE attendance 
                SET duration_hours = ?
                WHERE id = ?
            ''', (duration_hours, record_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ تم Update مدة العمل: {duration_hours} ساعة")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error في Update مدة العمل: {e}")
            return False
    
    # === دوال إدارة الإعدادات المحسنة ===
    
    def get_language_setting(self) -> str:
        """الحصول على إعداد اللغة الحالي"""
        try:
            return self.get_setting('language', 'ar')
        except Exception as e:
            logger.error(f"❌ Error في الحصول على إعداد اللغة: {e}")
            return 'ar'
    
    def get_theme_setting(self) -> str:
        """الحصول على إعداد الثيم الحالي"""
        try:
            return self.get_setting('theme', 'light')
        except Exception as e:
            logger.error(f"❌ Error في الحصول على إعداد الثيم: {e}")
            return 'light'
    
    def apply_language_setting(self, language_code: str) -> bool:
        """تطبيق إعداد اللغة"""
        try:
            # Save اللغة في قاعدة البيانات المحلية
            if self.save_setting('language', language_code):
                logger.info(f"✅ تم تطبيق اللغة: {language_code}")
                return True
            else:
                logger.error(f"❌ Failed في تطبيق اللغة: {language_code}")
                return False
        except Exception as e:
            logger.error(f"❌ Error في تطبيق اللغة: {e}")
            return False
    
    def apply_theme_setting(self, theme: str) -> bool:
        """تطبيق إعداد الثيم"""
        try:
            # Save الثيم في قاعدة البيانات المحلية
            if self.save_setting('theme', theme):
                logger.info(f"✅ تم تطبيق الثيم: {theme}")
                return True
            else:
                logger.error(f"❌ Failed في تطبيق الثيم: {theme}")
                return False
        except Exception as e:
            logger.error(f"❌ Error في تطبيق الثيم: {e}")
            return False
    
    def refresh_settings(self) -> Dict:
        """Update الإعدادات من قاعدة البيانات المحلية"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT key, value FROM app_settings')
            rows = cursor.fetchall()
            conn.close()
            
            settings = {}
            for row in rows:
                settings[row[0]] = row[1]
            
            # Add إعدادات افتراضية إذا لم توجد
            default_settings = {
                'theme': 'light',
                'language': 'ar',
                'auto_backup': 'true',
                'sync_interval': '30'
            }
            
            for key, value in default_settings.items():
                if key not in settings:
                    settings[key] = value
            
            return settings
            
        except Exception as e:
            logger.error(f"❌ Error في Update الإعدادات: {e}")
            return {}
    
    def reset_settings_to_defaults(self) -> bool:
        """إعادة تعيين الإعدادات إلى القيم الافتراضية"""
        try:
            default_settings = {
                'theme': 'light',
                'language': 'ar',
                'auto_backup': 'true',
                'sync_interval': '30'
            }
            
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # مسح الإعدادات الحالية
            cursor.execute('DELETE FROM app_settings')
            
            # Add الإعدادات الافتراضية
            for key, value in default_settings.items():
                cursor.execute('''
                    INSERT INTO app_settings (key, value)
                    VALUES (?, ?)
                ''', (key, value))
            
            conn.commit()
            conn.close()
            
            logger.info("✅ تم إعادة تعيين الإعدادات إلى القيم الافتراضية")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error في إعادة تعيين الإعدادات: {e}")
            return False
    
    # === دوال التحكم الكامل ===
    
    def get_control_panel(self) -> Dict:
        """الحصول على لوحة التحكم الكاملة"""
        return {
            'system_status': self.get_system_status(),
            'sync_settings': self.control_settings.copy(),
            'detailed_stats': self.detailed_stats.copy(),
            'sync_queue_status': self.get_sync_queue_detailed(),
            'performance_metrics': self.get_performance_metrics(),
            'error_log': self.get_recent_errors(),
            'thread_status': self.get_thread_status()
        }
    
    def get_system_status(self) -> Dict:
        """الحصول على حالة النظام الهجين"""
        try:
            return {
                'system_name': 'Simple Hybrid Manager - Supabase First',
                'version': '2.0',
                'status': 'Running' if self.sync_running else 'Stopped',
                'hybrid_mode': True,
                'supabase_first': self.supabase_first,
                'instant_sync': self.instant_sync,
                'sync_interval': self.sync_interval,
                'supabase_sync_interval': self.supabase_sync_interval,
                'sync_threads': {
                    'main_sync': hasattr(self, 'sync_thread') and self.sync_thread.is_alive() if hasattr(self, 'sync_thread') else False,
                    'supabase_sync': hasattr(self, 'supabase_sync_thread') and self.supabase_sync_thread.is_alive() if hasattr(self, 'supabase_sync_thread') else False,
                    'instant_sync': hasattr(self, 'instant_sync_thread') and self.instant_sync_thread.is_alive() if hasattr(self, 'instant_sync_thread') else False
                },
                'control_settings': self.control_settings,
                'detailed_stats': self.detailed_stats,
                'last_sync': self.detailed_stats.get('last_sync_time'),
                'last_supabase_sync': self.detailed_stats.get('last_supabase_sync_time'),
                'database_path': self.local_db_path,
                'supabase_connected': self.supabase_manager is not None
            }
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على حالة النظام: {e}")
            return {
                'system_name': 'Simple Hybrid Manager - Error',
                'status': 'Error',
                'error': str(e)
            }
    
    def update_control_settings(self, new_settings: Dict) -> bool:
        """Update إعدادات التحكم"""
        try:
            for key, value in new_settings.items():
                if key in self.control_settings:
                    self.control_settings[key] = value
                    logger.info(f"✅ تم Update إعداد التحكم: {key} = {value}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error في Update إعدادات التحكم: {e}")
            return False
    
    def pause_sync(self) -> bool:
        """إيقاف المزامنة مؤقتاً"""
        try:
            self.sync_running = False
            logger.info("⏸️ تم إيقاف المزامنة مؤقتاً")
            return True
        except Exception as e:
            logger.error(f"❌ Error في إيقاف المزامنة: {e}")
            return False
    
    def resume_sync(self) -> bool:
        """استئناف المزامنة"""
        try:
            self.sync_running = True
            logger.info("▶️ تم استئناف المزامنة")
            return True
        except Exception as e:
            logger.error(f"❌ Error في استئناف المزامنة: {e}")
            return False
    
    def force_full_sync(self) -> Dict:
        """إجبار مزامنة كاملة مع Supabase"""
        try:
            logger.info("🔄 بدء مزامنة كاملة إجبارية...")
            
            # مزامنة من البرنامج إلى Supabase
            self._process_sync_queue()
            self._process_memory_queue()
            
            # مزامنة من Supabase إلى البرنامج
            self._sync_from_supabase_to_local()
            
            # Update الإحصائيات
            self.detailed_stats['last_sync_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.detailed_stats['last_supabase_sync_time'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info("✅ تم إكمال المزامنة الكاملة الإجبارية")
            
            return {
                'status': 'success',
                'message': 'تم إكمال المزامنة الكاملة بنجاح',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
        except Exception as e:
            logger.error(f"❌ Error في المزامنة الكاملة: {e}")
            return {
                'status': 'error',
                'message': f'Failed في المزامنة الكاملة: {str(e)}',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def force_supabase_sync(self) -> Dict:
        """إجبار مزامنة فورية من Supabase"""
        logger.info("📥 إجبار مزامنة فورية من Supabase...")
        start_time = time.time()
        
        try:
            # مزامنة فورية من Supabase
            self._sync_from_supabase_to_local()
            
            end_time = time.time()
            duration = end_time - start_time
            
            result = {
                'success': True,
                'duration': f"{duration:.2f} ثانية",
                'supabase_sync': True,
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            logger.info(f"📥 اكتملت المزامنة الفورية من Supabase في {duration:.2f} ثانية")
            return result
            
        except Exception as e:
            logger.error(f"❌ Failedت المزامنة الفورية من Supabase: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
    
    def get_sync_queue_detailed(self) -> Dict:
        """الحصول على تفاصيل قائمة المزامنة"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # إحصائيات عامة
            cursor.execute('''
                SELECT status, COUNT(*) 
                FROM sync_queue 
                GROUP BY status
            ''')
            status_counts = dict(cursor.fetchall())
            
            # العمليات حسب النوع
            cursor.execute('''
                SELECT table_name, operation, COUNT(*) 
                FROM sync_queue 
                WHERE status = 'pending'
                GROUP BY table_name, operation
            ''')
            pending_by_type = cursor.fetchall()
            
            # أحدث العمليات
            cursor.execute('''
                SELECT table_name, operation, created_at, status, retry_count
                FROM sync_queue 
                ORDER BY created_at DESC 
                LIMIT 20
            ''')
            recent_operations = cursor.fetchall()
            
            conn.close()
            
            return {
                'status_counts': status_counts,
                'pending_by_type': pending_by_type,
                'recent_operations': recent_operations,
                'total_pending': status_counts.get('pending', 0),
                'total_synced': status_counts.get('synced', 0),
                'total_failed': status_counts.get('failed', 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على تفاصيل قائمة المزامنة: {e}")
            return {}
    
    def clear_sync_queue(self) -> bool:
        """مسح قائمة انتظار المزامنة"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM sync_queue')
            conn.commit()
            conn.close()
            
            # مسح قائمة الذاكرة أيضاً
            if hasattr(self, 'sync_queue'):
                while not self.sync_queue.empty():
                    try:
                        self.sync_queue.get_nowait()
                    except:
                        break
            
            logger.info("🗑️ تم مسح قائمة انتظار المزامنة")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error في مسح قائمة انتظار المزامنة: {e}")
            return False
    
    def get_sync_queue_count(self) -> int:
        """الحصول على عدد العمليات في قائمة انتظار المزامنة"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM sync_queue WHERE status = "pending"')
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على عدد العمليات: {e}")
            return 0
    
    def _check_local_db_connection(self) -> bool:
        """فحص اتصال قاعدة البيانات المحلية"""
        try:
            conn = sqlite3.connect(self.local_db_path, timeout=5.0)
            cursor = conn.cursor()
            cursor.execute('SELECT 1')
            conn.close()
            return True
        except Exception:
            return False
    
    def _check_supabase_connection(self) -> bool:
        """فحص اتصال Supabase"""
        try:
            if self.supabase_manager is None:
                self.supabase_manager = SupabaseManager()
            
            # محاولة عملية بسيطة
            self.supabase_manager.get_all_employees()
            return True
        except Exception:
            return False
    
    def shutdown(self):
        """إيقاف النظام الهجين وDelete قاعدة البيانات المحلية"""
        try:
            logger.info("🔄 إيقاف النظام الهجين - Supabase First...")
            
            # إيقاف المزامنة
            self.sync_running = False
            
            # انتظار انتهاء جميع الخيوط
            threads_to_join = []
            
            if hasattr(self, 'sync_thread') and self.sync_thread:
                if self.sync_thread.is_alive():
                    threads_to_join.append(self.sync_thread)
            
            if hasattr(self, 'supabase_sync_thread') and self.supabase_sync_thread:
                if self.supabase_sync_thread.is_alive():
                    threads_to_join.append(self.supabase_sync_thread)
            
            if hasattr(self, 'instant_sync_thread') and self.instant_sync_thread:
                if self.instant_sync_thread.is_alive():
                    threads_to_join.append(self.instant_sync_thread)
            
            # انتظار انتهاء الخيوط
            for thread in threads_to_join:
                thread.join(timeout=3)
            
            # مزامنة أخيرة مع Supabase
            try:
                logger.info("🔄 إجراء مزامنة أخيرة مع Supabase...")
                self._process_sync_queue()
                self._process_memory_queue()
                logger.info("✅ تم إجراء مزامنة أخيرة مع Supabase")
            except Exception as e:
                logger.warning(f"⚠️ Error في المزامنة الأخيرة: {e}")
            
            # 🗑️ Delete قاعدة البيانات المحلية (Supabase First)
            if self.control_settings.get('delete_local_on_exit', True):
                try:
                    self._delete_local_database()
                    logger.info("🗑️ تم Delete قاعدة البيانات المحلية بنجاح")
                except Exception as e:
                    logger.warning(f"⚠️ Error في Delete قاعدة البيانات المحلية: {e}")
            
            logger.info("🛑 تم إيقاف النظام الهجين - Supabase First بنجاح")
            
        except Exception as e:
            logger.error(f"❌ Error في إيقاف النظام الهجين: {e}")
    
    def _delete_local_database(self):
        """Delete قاعدة البيانات المحلية"""
        try:
            import os
            
            # Close جميع الاتصالات
            if hasattr(self, '_close_all_connections'):
                self._close_all_connections()
            
            # Delete ملف قاعدة البيانات
            if os.path.exists(self.local_db_path):
                os.remove(self.local_db_path)
                logger.info(f"🗑️ تم Delete {self.local_db_path}")
            
            # Delete ملفات النسخ الاحتياطية
            backup_files = [f for f in os.listdir('.') if f.startswith('backup_') and f.endswith('.db')]
            for backup_file in backup_files:
                try:
                    os.remove(backup_file)
                    logger.info(f"🗑️ تم Delete النسخة الاحتياطية: {backup_file}")
                except Exception as e:
                    logger.warning(f"⚠️ Error في Delete النسخة الاحتياطية {backup_file}: {e}")
            
        except Exception as e:
            logger.error(f"❌ Error في Delete قاعدة البيانات المحلية: {e}")
            raise
    
    def _close_all_connections(self):
        """Close جميع الاتصالات بقاعدة البيانات"""
        try:
            # Close الاتصالات المفتوحة
            if hasattr(self, '_active_connections'):
                for conn in self._active_connections:
                    try:
                        if conn:
                            conn.close()
                    except Exception:
                        pass
                self._active_connections.clear()
            
            logger.info("🔒 تم Close جميع الاتصالات بقاعدة البيانات")
            
        except Exception as e:
            logger.warning(f"⚠️ Error في Close الاتصالات: {e}")
    
    def __getattr__(self, name):
        """توجيه باقي الدوال إلى المدير الأصلي"""
        if self.original_db is None:
            self.original_db = DatabaseManager()
        return getattr(self.original_db, name)
    
    def update_employee_qr_code(self, employee_id: int, qr_code: str) -> bool:
        """Update employee QR code مع مزامنة فورية"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE employees 
                SET qr_code = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (qr_code, employee_id))
            
            conn.commit()
            conn.close()
            
            # مزامنة فورية مع Supabase
            update_data = {'qr_code': qr_code}
            self._immediate_sync("employees", employee_id, "UPDATE", update_data)
            self._add_to_sync_queue("employees", employee_id, "UPDATE", update_data)
            
            logger.info(f"✅ تم Update employee QR code: ID {employee_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error في Update employee QR code: {e}")
            return False
    
    def get_attendance_by_employee_date(self, employee_id: int, date: str) -> Optional[Dict]:
        """الحصول على سجل حضور موظف في تاريخ محدد"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, employee_id, check_time, date, type, notes, location_id
                FROM attendance 
                WHERE employee_id = ? AND date = ?
                ORDER BY check_time DESC
                LIMIT 1
            ''', (employee_id, date))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'employee_id': result[1],
                    'check_time': result[2],
                    'date': result[3],
                    'type': result[4],
                    'notes': result[5],
                    'location_id': result[6]
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على سجل الحضور: {e}")
            return None
    
    def get_employee_attendance_history(self, employee_id: int) -> List[Dict]:
        """الحصول على تاريخ حضور موظف"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, check_time, date, type, notes, location_id
                FROM attendance 
                WHERE employee_id = ?
                ORDER BY date DESC, check_time DESC
            ''', (employee_id,))
            
            rows = cursor.fetchall()
            conn.close()
            
            history = []
            for row in rows:
                history.append({
                    'id': row[0],
                    'check_time': row[1],
                    'date': row[2],
                    'type': row[3],
                    'notes': row[4],
                    'location_id': row[5]
                })
            
            return history
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على تاريخ الحضور: {e}")
            return []
    

    
    def add_attendance(self, attendance_data: Dict) -> Optional[int]:
        """Add سجل حضور (للتوافق مع النظام التقليدي)"""
        return self.record_attendance(attendance_data)
    
    def get_web_sync_status(self) -> Dict:
        """الحصول على حالة المزامنة مع الويب"""
        try:
            return {
                'web_sync_enabled': True,
                'web_sync_active': True,
                'last_web_sync': self.detailed_stats.get('last_supabase_sync_time'),
                'web_sync_interval': self.supabase_sync_interval,
                'web_sync_errors': []
            }
        except Exception as e:
            logger.error(f"❌ Error في الحصول على حالة مزامنة الويب: {e}")
            return {
                'web_sync_enabled': False,
                'web_sync_active': False,
                'last_web_sync': None,
                'web_sync_interval': 0,
                'web_sync_errors': [str(e)]
            }
    
    def get_sync_status(self) -> Dict:
        """الحصول على حالة المزامنة للنظام الهجين"""
        try:
            return {
                'hybrid_mode': True,
                'supabase_disabled': False,
                'initial_sync_completed': True,
                'sync_in_progress': False,
                'last_sync': self.detailed_stats.get('last_sync_time'),
                'last_error': None,
                'pending_changes': 0,  # سيتم Updateها لاحقاً
                'sync_enabled': self.control_settings.get('sync_enabled', True),
                'instant_sync': self.control_settings.get('instant_sync', True),
                'supabase_first': self.control_settings.get('supabase_first', True)
            }
        except Exception as e:
            logger.error(f"❌ Error في الحصول على حالة المزامنة: {e}")
            return {
                'hybrid_mode': False,
                'supabase_disabled': True,
                'initial_sync_completed': False,
                'sync_in_progress': False,
                'last_sync': None,
                'last_error': str(e),
                'pending_changes': 0,
                'sync_enabled': False,
                'instant_sync': False,
                'supabase_first': False
            }
    
    def get_employee_by_phone(self, phone_number: str) -> Optional[Dict]:
        """الحصول على موظف بواسطة رقم الهاتف"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, employee_code, name, job_title, department, phone_number, web_fingerprint, device_token, qr_code
                FROM employees WHERE phone_number = ?
            ''', (phone_number,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'employee_code': result[1],
                    'name': result[2],
                    'job_title': result[3] or '',
                    'department': result[4] or '',
                    'phone_number': result[5] or '',
                    'web_fingerprint': result[6] or '',
                    'device_token': result[7] or '',
                    'qr_code': result[8] or ''
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على الموظف: {e}")
            return None
    
    def get_employee_by_token(self, device_token: str) -> Optional[Dict]:
        """الحصول على موظف بواسطة device_token"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, employee_code, name, job_title, department, phone_number, web_fingerprint, device_token, qr_code
                FROM employees WHERE device_token = ?
            ''', (device_token,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'employee_code': result[1],
                    'name': result[2],
                    'job_title': result[3] or '',
                    'department': result[4] or '',
                    'phone_number': result[5] or '',
                    'web_fingerprint': result[6] or '',
                    'device_token': result[7] or '',
                    'qr_code': result[8] or ''
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على الموظف بواسطة token: {e}")
            return None
    
    def execute_query(self, query: str, params: tuple = (), commit: bool = False, fetch: bool = False):
        """تنفيذ استعلام SQL مع مزامنة فورية"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute(query, params)
            
            if commit:
                conn.commit()
                
                # إذا كان الاستعلام يعدل بيانات الموظفين، أضف للمزامنة
                if 'UPDATE employees' in query.upper() and 'device_token' in query:
                    # استخراج employee_id من المعاملات
                    if params and len(params) >= 2:
                        employee_id = params[-1]  # آخر معامل هو عادة employee_id
                        self._add_to_sync_queue("employees", employee_id, "UPDATE", {
                            'device_token': params[0] if len(params) >= 1 else None
                        })
                        self._immediate_sync("employees", employee_id, "UPDATE", {
                            'device_token': params[0] if len(params) >= 1 else None
                        })
            
            if fetch:
                result = cursor.fetchall()
                conn.close()
                return result
            else:
                conn.close()
                return True
                
        except Exception as e:
            logger.error(f"❌ Error في تنفيذ الاستعلام: {e}")
            return False
    
    def get_employee_by_name(self, name: str) -> Optional[Dict]:
        """الحصول على موظف بواسطة الاسم"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, employee_code, name, job_title, department, phone_number, qr_code
                FROM employees WHERE name = ?
            ''', (name,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'employee_code': result[1],
                    'name': result[2],
                    'job_title': result[3] or '',
                    'department': result[4] or '',
                    'phone_number': result[5] or '',
                    'qr_code': result[6] or ''
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على الموظف: {e}")
            return None
    
    def get_employee_by_fingerprint(self, fingerprint_data: str) -> Optional[Dict]:
        """الحصول على موظف بواسطة بيانات البصمة"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, employee_code, name, job_title, department, phone_number, qr_code
                FROM employees WHERE fingerprint_data = ?
            ''', (fingerprint_data,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'employee_code': result[1],
                    'name': result[2],
                    'job_title': result[3] or '',
                    'department': result[4] or '',
                    'phone_number': result[5] or '',
                    'qr_code': result[6] or ''
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على الموظف: {e}")
            return None
    
    def get_employee_by_qr_code(self, qr_code: str) -> Optional[Dict]:
        """الحصول على موظف بواسطة رمز QR"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, employee_code, name, job_title, department, phone_number, qr_code
                FROM employees WHERE qr_code = ?
            ''', (qr_code,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'employee_code': result[1],
                    'name': result[2],
                    'job_title': result[3] or '',
                    'department': result[4] or '',
                    'phone_number': result[5] or '',
                    'qr_code': result[6] or ''
                }
            return None
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على الموظف: {e}")
            return None
    
    def get_attendance_by_date(self, date: str) -> List[Dict]:
        """الحصول على سجلات الحضور في تاريخ محدد"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT a.id, a.employee_id, a.check_time, a.date, a.type, a.notes, a.location_id,
                       e.name as employee_name, l.name as location_name
                FROM attendance a
                LEFT JOIN employees e ON a.employee_id = e.id
                LEFT JOIN locations l ON a.location_id = l.id
                WHERE a.date = ?
                ORDER BY a.check_time ASC
            ''', (date,))
            
            rows = cursor.fetchall()
            conn.close()
            
            records = []
            for row in rows:
                records.append({
                    'id': row[0],
                    'employee_id': row[1],
                    'check_time': row[2],
                    'date': row[3],
                    'type': row[4],
                    'notes': row[5],
                    'location_id': row[6],
                    'employee_name': row[7] or 'Unknown',
                    'location_name': row[8] or 'N/A'
                })
            
            return records
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على سجلات الحضور: {e}")
            return []
    
    def get_employee_by_job_title(self, job_title: str) -> List[Dict]:
        """الحصول على موظفين بواسطة المسمى الوظيفي"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, employee_code, name, job_title, department, phone_number, qr_code
                FROM employees WHERE job_title = ?
                ORDER BY name
            ''', (job_title,))
            
            rows = cursor.fetchall()
            conn.close()
            
            employees = []
            for row in rows:
                employees.append({
                    'id': row[0],
                    'employee_code': row[1],
                    'name': row[2],
                    'job_title': row[3] or '',
                    'department': row[4] or '',
                    'phone_number': row[5] or '',
                    'qr_code': row[6] or ''
                })
            
            return employees
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على الموظفين: {e}")
            return []
    
    def get_employee_by_department(self, department: str) -> List[Dict]:
        """الحصول على موظفين بواسطة القسم"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, employee_code, name, job_title, department, phone_number, qr_code
                FROM employees WHERE department = ?
                ORDER BY name
            ''', (department,))
            
            rows = cursor.fetchall()
            conn.close()
            
            employees = []
            for row in rows:
                employees.append({
                    'id': row[0],
                    'employee_code': row[1],
                    'name': row[2],
                    'job_title': row[3] or '',
                    'department': row[4] or '',
                    'phone_number': row[5] or '',
                    'qr_code': row[6] or ''
                })
            
            return employees
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على الموظفين: {e}")
            return []
    
    def get_attendance_statistics(self, start_date: str = None, end_date: str = None) -> Dict:
        """الحصول على إحصائيات الحضور"""
        try:
            if not start_date:
                from datetime import datetime, timedelta
                end_date = datetime.now().strftime('%Y-%m-%d')
                start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # إجمالي سجلات الحضور
            cursor.execute('''
                SELECT COUNT(*) FROM attendance 
                WHERE date BETWEEN ? AND ?
            ''', (start_date, end_date))
            total_records = cursor.fetchone()[0]
            
            # سجلات الحضور
            cursor.execute('''
                SELECT COUNT(*) FROM attendance 
                WHERE date BETWEEN ? AND ? AND type = 'Check-In'
            ''', (start_date, end_date))
            check_in_records = cursor.fetchone()[0]
            
            # سجلات الانصراف
            cursor.execute('''
                SELECT COUNT(*) FROM attendance 
                WHERE date BETWEEN ? AND ? AND type = 'Check-Out'
            ''', (start_date, end_date))
            check_out_records = cursor.fetchone()[0]
            
            # الموظفين الActiveين
            cursor.execute('''
                SELECT COUNT(DISTINCT employee_id) FROM attendance 
                WHERE date BETWEEN ? AND ?
            ''', (start_date, end_date))
            active_employees = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'period': {'start': start_date, 'end': end_date},
                'total_records': total_records,
                'check_in_records': check_in_records,
                'check_out_records': check_out_records,
                'active_employees': active_employees,
                'average_daily_records': total_records / max(1, (datetime.strptime(end_date, '%Y-%m-%d') - datetime.strptime(start_date, '%Y-%m-%d')).days)
            }
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على إحصائيات الحضور: {e}")
            return {}
    
    def get_attendance_summary(self, date: str = None) -> Dict:
        """الحصول على ملخص الحضور لليوم"""
        try:
            if not date:
                from datetime import datetime
                date = datetime.now().strftime('%Y-%m-%d')
            
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # إجمالي الموظفين
            cursor.execute('SELECT COUNT(*) FROM employees')
            total_employees = cursor.fetchone()[0]
            
            # الموظفين الحاضرين
            cursor.execute('''
                SELECT COUNT(DISTINCT employee_id) 
                FROM attendance 
                WHERE date = ? AND type = 'Check-In'
            ''', (date,))
            present_employees = cursor.fetchone()[0]
            
            # الموظفين المنصرفين
            cursor.execute('''
                SELECT COUNT(DISTINCT employee_id) 
                FROM attendance 
                WHERE date = ? AND type = 'Check-Out'
            ''', (date,))
            left_employees = cursor.fetchone()[0]
            
            # الموظفين المتأخرين (يمكن Add منطق أكثر تعقيداً هنا)
            late_employees = 0
            
            conn.close()
            
            return {
                'date': date,
                'total_employees': total_employees,
                'present_employees': present_employees,
                'left_employees': left_employees,
                'late_employees': late_employees,
                'absent_employees': total_employees - present_employees
            }
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على ملخص الحضور: {e}")
            return {}
    
    def get_employee_attendance_by_date_range(self, employee_id: int, start_date: str, end_date: str) -> List[Dict]:
        """الحصول على حضور موظف في نطاق تاريخي"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, check_time, date, type, notes, location_id
                FROM attendance 
                WHERE employee_id = ? AND date BETWEEN ? AND ?
                ORDER BY date DESC, check_time DESC
            ''', (employee_id, start_date, end_date))
            
            rows = cursor.fetchall()
            conn.close()
            
            records = []
            for row in rows:
                records.append({
                    'id': row[0],
                    'check_time': row[1],
                    'date': row[2],
                    'type': row[3],
                    'notes': row[4],
                    'location_id': row[5]
                })
            
            return records
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على حضور الموظف: {e}")
            return []
    
    def get_attendance_count(self, date: str = None) -> int:
        """الحصول على عدد سجلات الحضور لليوم"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            if date:
                cursor.execute('SELECT COUNT(*) FROM attendance WHERE date = ?', (date,))
            else:
                cursor.execute('SELECT COUNT(*) FROM attendance')
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على عدد سجلات الحضور: {e}")
            return 0
    
    def get_user_count(self) -> int:
        """الحصول على عدد المستخدمين"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM users')
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على عدد المستخدمين: {e}")
            return 0
    
    def get_employee_count(self) -> int:
        """الحصول على عدد الموظفين"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM employees')
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على عدد الموظفين: {e}")
            return 0
    
    def get_sync_queue_info(self) -> Dict:
        """الحصول على Information قائمة انتظار المزامنة"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # إجمالي العمليات في قائمة الانتظار
            cursor.execute('SELECT COUNT(*) FROM sync_queue WHERE status = "pending"')
            pending_count = cursor.fetchone()[0]
            
            # العمليات المزامنة
            cursor.execute('SELECT COUNT(*) FROM sync_queue WHERE status = "synced"')
            synced_count = cursor.fetchone()[0]
            
            # العمليات الفاشلة
            cursor.execute('SELECT COUNT(*) FROM sync_queue WHERE status = "failed"')
            failed_count = cursor.fetchone()[0]
            
            # آخر 10 عمليات
            cursor.execute('''
                SELECT table_name, record_id, operation, status, created_at, synced_at
                FROM sync_queue 
                ORDER BY created_at DESC 
                LIMIT 10
            ''')
            recent_operations = []
            for row in cursor.fetchall():
                recent_operations.append({
                    'table_name': row[0],
                    'record_id': row[1],
                    'operation': row[2],
                    'status': row[3],
                    'created_at': row[4],
                    'synced_at': row[5]
                })
            
            conn.close()
            
            return {
                'pending_operations': pending_count,
                'synced_operations': synced_count,
                'failed_operations': failed_count,
                'total_operations': pending_count + synced_count + failed_count,
                'recent_operations': recent_operations,
                'memory_queue_size': self.sync_queue.qsize() if hasattr(self, 'sync_queue') else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على Information قائمة انتظار المزامنة: {e}")
            return {}
    
    def get_database_info(self) -> Dict:
        """الحصول على Information قاعدة البيانات"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # Information الجداول
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # حجم قاعدة البيانات
            import os
            db_size = os.path.getsize(self.local_db_path) if os.path.exists(self.local_db_path) else 0
            
            # عدد السجلات في كل جدول
            table_counts = {}
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_counts[table] = count
                except:
                    table_counts[table] = 0
            
            conn.close()
            
            return {
                'database_path': self.local_db_path,
                'database_size_bytes': db_size,
                'database_size_mb': round(db_size / (1024 * 1024), 2),
                'tables': tables,
                'table_counts': table_counts,
                'total_records': sum(table_counts.values()),
                'last_sync': self.detailed_stats.get('last_sync_time'),
                'last_supabase_sync': self.detailed_stats.get('last_supabase_sync_time')
            }
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على Information قاعدة البيانات: {e}")
            return {}
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """الحصول على الأخطاء الحديثة"""
        try:
            errors = self.detailed_stats.get('sync_errors', [])
            return errors[-limit:] if errors else []
        except Exception as e:
            logger.error(f"❌ Error في الحصول على الأخطاء الحديثة: {e}")
            return []
    
    def get_performance_metrics(self) -> Dict:
        """الحصول على مقاييس الأداء"""
        try:
            total_ops = self.detailed_stats['total_operations']
            success_rate = (self.detailed_stats['successful_operations'] / total_ops * 100) if total_ops > 0 else 0
            
            return {
                'success_rate': f"{success_rate:.1f}%",
                'total_operations': total_ops,
                'successful_operations': self.detailed_stats['successful_operations'],
                'failed_operations': self.detailed_stats['failed_operations'],
                'duplicate_operations': self.detailed_stats['duplicate_operations'],
                'retry_operations': self.detailed_stats['retry_operations'],
                'average_sync_time': "2-5 ثوانِ",
                'last_sync_time': self.detailed_stats['last_sync_time'],
                'memory_queue_size': self.sync_queue.qsize() if hasattr(self, 'sync_queue') else 0,
                'active_threads': len([t for t in self.sync_thread_pool if t.is_alive()]) if hasattr(self, 'sync_thread_pool') else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error في حساب مقاييس الأداء: {e}")
            return {}
    
    def get_thread_status(self) -> Dict:
        """الحصول على حالة الخيوط"""
        try:
            active_threads = [t for t in self.sync_thread_pool if t.is_alive()] if hasattr(self, 'sync_thread_pool') else []
            return {
                'main_sync_thread_alive': hasattr(self, 'sync_thread') and self.sync_thread.is_alive(),
                'supabase_sync_thread_alive': hasattr(self, 'supabase_sync_thread') and self.supabase_sync_thread.is_alive(),
                'instant_sync_thread_alive': hasattr(self, 'instant_sync_thread') and self.instant_sync_thread.is_alive(),
                'active_sync_threads': len(active_threads),
                'max_threads': self.control_settings.get('max_sync_threads', 10),
                'threads_usage': f"{len(active_threads)}/{self.control_settings.get('max_sync_threads', 10)}"
            }
        except Exception as e:
            logger.error(f"❌ Error في الحصول على حالة الخيوط: {e}")
            return {}
    
    def reset_statistics(self):
        """إعادة تعيين الإحصائيات"""
        try:
            self.detailed_stats = {
                'total_operations': 0,
                'successful_operations': 0,
                'failed_operations': 0,
                'duplicate_operations': 0,
                'retry_operations': 0,
                'last_sync_time': None,
                'last_supabase_sync_time': None,
                'sync_errors': [],
                'performance_metrics': {}
            }
            logger.info("📊 تم إعادة تعيين الإحصائيات")
        except Exception as e:
            logger.error(f"❌ Error في إعادة تعيين الإحصائيات: {e}")
    
    def export_data(self, format: str = 'json') -> Dict:
        """تصدير البيانات"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if format == 'json':
                export_data = {
                    'employees': self.get_all_employees(),
                    'users': self.get_all_users(),
                    'locations': self.get_all_locations(),
                    'holidays': self.get_all_holidays(),
                    'settings': self.get_all_settings(),
                    'export_info': {
                        'timestamp': timestamp,
                        'version': '1.0',
                        'total_records': 0
                    }
                }
                
                # حساب إجمالي السجلات
                export_data['export_info']['total_records'] = (
                    len(export_data['employees']) + 
                    len(export_data['users']) + 
                    len(export_data['locations']) + 
                    len(export_data['holidays'])
                )
                
                export_file = f"data_export_{timestamp}.json"
                
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, ensure_ascii=False, indent=2)
                
                logger.info(f"📤 تم تصدير البيانات: {export_file}")
                
                return {
                    'success': True,
                    'export_file': export_file,
                    'format': format,
                    'total_records': export_data['export_info']['total_records'],
                    'size': os.path.getsize(export_file)
                }
            
        except Exception as e:
            logger.error(f"❌ Failed في تصدير البيانات: {e}")
            return {'success': False, 'error': str(e)}
    
    def create_backup(self) -> Dict:
        """إنشاء نسخة احتياطية"""
        try:
            if not self.control_settings.get('backup_enabled', True):
                return {'success': False, 'message': 'النسخ الاحتياطي Disabled'}
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = f"backup_local_attendance_{timestamp}.db"
            
            # نسخ قاعدة البيانات المحلية
            import shutil
            shutil.copy2(self.local_db_path, backup_path)
            
            logger.info(f"💾 تم إنشاء نسخة احتياطية: {backup_path}")
            
            return {
                'success': True,
                'backup_path': backup_path,
                'timestamp': timestamp,
                'size': os.path.getsize(backup_path)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed في إنشاء النسخة الاحتياطية: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_control_panel_info(self) -> Dict:
        """الحصول على Information لوحة التحكم الكاملة"""
        try:
            return {
                'system_status': self.get_system_status(),
                'sync_status': self.get_sync_status(),
                'web_sync_status': self.get_web_sync_status(),
                'database_info': self.get_database_info(),
                'sync_queue_info': self.get_sync_queue_info(),
                'performance_metrics': self.get_performance_metrics(),
                'thread_status': self.get_thread_status(),
                'recent_errors': self.get_recent_errors(5),
                'employee_count': self.get_employee_count(),
                'user_count': self.get_user_count(),
                'attendance_count': self.get_attendance_count(),
                'attendance_summary': self.get_attendance_summary(),
                'attendance_statistics': self.get_attendance_statistics(),
                'control_settings': self.control_settings,
                'detailed_stats': self.detailed_stats
            }
        except Exception as e:
            logger.error(f"❌ Error في الحصول على Information لوحة التحكم: {e}")
            return {
                'error': str(e),
                'status': 'error'
            }
    
    def get_sync_queue_detailed(self) -> Dict:
        """الحصول على تفاصيل قائمة انتظار المزامنة"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # إحصائيات عامة
            cursor.execute('''
                SELECT status, COUNT(*) 
                FROM sync_queue 
                GROUP BY status
            ''')
            status_counts = dict(cursor.fetchall())
            
            # العمليات حسب النوع
            cursor.execute('''
                SELECT table_name, operation, COUNT(*) 
                FROM sync_queue 
                WHERE status = 'pending'
                GROUP BY table_name, operation
            ''')
            pending_by_type = cursor.fetchall()
            
            # أحدث العمليات
            cursor.execute('''
                SELECT table_name, operation, created_at, status, retry_count
                FROM sync_queue 
                ORDER BY created_at DESC 
                LIMIT 20
            ''')
            recent_operations = cursor.fetchall()
            
            conn.close()
            
            return {
                'status_counts': status_counts,
                'pending_by_type': pending_by_type,
                'recent_operations': recent_operations,
                'total_pending': status_counts.get('pending', 0),
                'total_synced': status_counts.get('synced', 0),
                'total_failed': status_counts.get('failed', 0)
            }
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على تفاصيل قائمة انتظار المزامنة: {e}")
            return {}
    

    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """الحصول على الأخطاء الأخيرة"""
        try:
            # جمع الأخطاء من الذاكرة
            errors = []
            if hasattr(self, '_error_log'):
                errors = self._error_log[-limit:]
            
            return [
                {
                    'timestamp': error.get('timestamp', ''),
                    'error_type': error.get('type', ''),
                    'message': error.get('message', ''),
                    'details': error.get('details', '')
                }
                for error in errors
            ]
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على الأخطاء الأخيرة: {e}")
            return []
    
    def get_thread_status(self) -> Dict:
        """الحصول على حالة الخيوط"""
        try:
            thread_status = {}
            
            # حالة الخيط الرئيسي
            if hasattr(self, 'sync_thread'):
                thread_status['main_sync'] = {
                    'alive': self.sync_thread.is_alive() if self.sync_thread else False,
                    'name': 'Main Sync Thread',
                    'daemon': getattr(self.sync_thread, 'daemon', False) if self.sync_thread else False
                }
            
            # حالة خيط مزامنة Supabase
            if hasattr(self, 'supabase_sync_thread'):
                thread_status['supabase_sync'] = {
                    'alive': self.supabase_sync_thread.is_alive() if self.supabase_sync_thread else False,
                    'name': 'Supabase Sync Thread',
                    'daemon': getattr(self.supabase_sync_thread, 'daemon', False) if self.supabase_sync_thread else False
                }
            
            # حالة خيط المزامنة الفورية
            if hasattr(self, 'instant_sync_thread'):
                thread_status['instant_sync'] = {
                    'alive': self.instant_sync_thread.is_alive() if self.instant_sync_thread else False,
                    'name': 'Instant Sync Thread',
                    'daemon': getattr(self.instant_sync_thread, 'daemon', False) if self.instant_sync_thread else False
                }
            
            # حالة خيوط المزامنة الإضافية
            if hasattr(self, 'sync_thread_pool'):
                thread_status['sync_pool'] = {
                    'total_threads': len(self.sync_thread_pool),
                    'alive_threads': len([t for t in self.sync_thread_pool if t.is_alive()]),
                    'max_threads': self.control_settings.get('max_sync_threads', 15)
                }
            
            return thread_status
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على حالة الخيوط: {e}")
            return {}
    
    def get_sync_queue_count(self) -> int:
        """الحصول على عدد العمليات في قائمة انتظار المزامنة"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM sync_queue WHERE status = "pending"')
            count = cursor.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على عدد العمليات: {e}")
            return 0
    
    def clear_sync_queue(self) -> bool:
        """مسح قائمة انتظار المزامنة"""
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM sync_queue')
            conn.commit()
            conn.close()
            
            # مسح قائمة الذاكرة أيضاً
            if hasattr(self, 'sync_queue'):
                while not self.sync_queue.empty():
                    try:
                        self.sync_queue.get_nowait()
                    except:
                        break
            
            logger.info("🗑️ تم مسح قائمة انتظار المزامنة")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error في مسح قائمة انتظار المزامنة: {e}")
            return False
    
    def health_check(self) -> Dict:
        """فحص صحة النظام"""
        try:
            health_status = {
                'overall_status': 'Healthy',
                'checks': {},
                'timestamp': datetime.now().isoformat()
            }
            
            # فحص قاعدة البيانات المحلية
            local_db_ok = self._check_local_db_connection()
            health_status['checks']['local_database'] = {
                'status': 'OK' if local_db_ok else 'ERROR',
                'message': 'Connected' if local_db_ok else 'Connection failed'
            }
            
            # فحص اتصال Supabase
            supabase_ok = self._check_supabase_connection()
            health_status['checks']['supabase'] = {
                'status': 'OK' if supabase_ok else 'ERROR',
                'message': 'Connected' if supabase_ok else 'Connection failed'
            }
            
            # فحص الخيوط
            threads_ok = all([
                hasattr(self, 'sync_thread') and self.sync_thread.is_alive(),
                hasattr(self, 'supabase_sync_thread') and self.supabase_sync_thread.is_alive(),
                hasattr(self, 'instant_sync_thread') and self.instant_sync_thread.is_alive()
            ])
            health_status['checks']['threads'] = {
                'status': 'OK' if threads_ok else 'ERROR',
                'message': 'All threads running' if threads_ok else 'Some threads stopped'
            }
            
            # تحديد الحالة العامة
            all_checks_ok = all(check['status'] == 'OK' for check in health_status['checks'].values())
            health_status['overall_status'] = 'Healthy' if all_checks_ok else 'Unhealthy'
            
            return health_status
            
        except Exception as e:
            logger.error(f"❌ Error في فحص صحة النظام: {e}")
            return {
                'overall_status': 'Error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    # 🆕 دوال كشف التغييرات الذكي
    def has_supabase_changes(self):
        """فحص وجود تغييرات في Supabase"""
        try:
            if not self.change_detection['enabled']:
                return False
            
            # فحص التغييرات كل دقيقة فقط
            now = datetime.now()
            if (self.change_detection['last_change_check'] and 
                (now - self.change_detection['last_change_check']).total_seconds() < self.change_detection['change_check_interval']):
                return self.change_detection['has_changes']
            
            # Update وقت آخر فحص
            self.change_detection['last_change_check'] = now
            
            # الحصول على hash البيانات الحالي من Supabase
            current_hash = self._get_supabase_data_hash()
            
            # مقارنة مع آخر hash معروف
            if current_hash != self.change_detection['last_supabase_hash']:
                self.change_detection['has_changes'] = True
                self.change_detection['last_change_time'] = now
                self.change_detection['change_count'] += 1
                logger.info(f"🔄 تم اكتشاف تغييرات في Supabase (التغيير رقم: {self.change_detection['change_count']})")
            else:
                self.change_detection['has_changes'] = False
            
            return self.change_detection['has_changes']
            
        except Exception as e:
            logger.error(f"❌ Error في فحص التغييرات: {e}")
            return False
    
    def force_full_sync(self):
        """إجبار مزامنة كاملة من Supabase"""
        try:
            logger.info("🔄 بدء المزامنة الإجبارية من Supabase...")
            
            # مزامنة كاملة من Supabase
            self._sync_from_supabase_to_local()
            
            # Update hash البيانات
            self.change_detection['last_supabase_hash'] = self._get_supabase_data_hash()
            self.change_detection['has_changes'] = False
            self.change_detection['change_types'] = []
            
            logger.info("✅ اكتملت المزامنة الإجبارية بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error في المزامنة الإجبارية: {e}")
            return False
    
    def get_change_info(self):
        """الحصول على Information التغييرات"""
        return {
            'has_changes': self.change_detection['has_changes'],
            'change_count': self.change_detection['change_count'],
            'last_change_time': self.change_detection['last_change_time'],
            'change_types': self.change_detection['change_types'],
            'last_check': self.change_detection['last_change_check']
        }
    
    def _get_supabase_data_hash(self):
        """الحصول على hash البيانات من Supabase"""
        try:
            if not self.supabase_manager:
                return None
            
            # جمع البيانات من جميع الجداول
            data_components = []
            
            # الموظفين
            employees = self.supabase_manager.get_all_employees() or []
            data_components.append(f"employees:{len(employees)}")
            
            # المستخدمين
            users = self.supabase_manager.get_all_users() or []
            data_components.append(f"users:{len(users)}")
            
            # سجلات الحضور
            attendance = self.supabase_manager.get_all_attendance() or []
            data_components.append(f"attendance:{len(attendance)}")
            
            # المواقع
            locations = self.supabase_manager.get_all_locations() or []
            data_components.append(f"locations:{len(locations)}")
            
            # الإجازات
            holidays = self.supabase_manager.get_all_holidays() or []
            data_components.append(f"holidays:{len(holidays)}")
            
            # الإعدادات
            settings = self.supabase_manager.get_all_settings() or {}
            data_components.append(f"settings:{len(settings)}")
            
            # إنشاء hash من البيانات
            import hashlib
            data_string = "|".join(data_components)
            return hashlib.md5(data_string.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"❌ Error في الحصول على hash البيانات: {e}")
            return None
    
    def emergency_shutdown(self):
        """إيقاف طارئ للنظام"""
        try:
            logger.warning("🚨 إيقاف طارئ للنظام...")
            
            # إيقاف فوري للمزامنة
            self.sync_running = False
            
            # إيقاف جميع الخيوط
            if hasattr(self, 'sync_thread') and self.sync_thread:
                self.sync_thread.join(timeout=1)
            
            if hasattr(self, 'supabase_sync_thread') and self.supabase_sync_thread:
                self.supabase_sync_thread.join(timeout=1)
            
            if hasattr(self, 'instant_sync_thread') and self.instant_sync_thread:
                self.instant_sync_thread.join(timeout=1)
            
            # إيقاف خيوط المزامنة الإضافية
            if hasattr(self, 'sync_thread_pool'):
                for thread in self.sync_thread_pool:
                    thread.join(timeout=1)
            
            logger.warning("🚨 تم إيقاف النظام الطارئ")
            
        except Exception as e:
            logger.error(f"❌ Error في الإيقاف الطارئ: {e}")
    
    def __del__(self):
        """دالة التنظيف عند Delete الكائن"""
        try:
            self.shutdown()
        except:
            pass

# === دوال مساعدة للتوافق ===

def create_simple_hybrid_manager():
    """إنشاء مدير هجين بسيط"""
    return SimpleHybridManager()

def get_simple_hybrid_manager():
    """الحصول على مدير هجين بسيط (Singleton)"""
    if not hasattr(get_simple_hybrid_manager, '_instance'):
        get_simple_hybrid_manager._instance = SimpleHybridManager()
    return get_simple_hybrid_manager._instance

# === اختبار النظام ===
if __name__ == "__main__":
    try:
        print("🚀 اختبار النظام الهجين البسيط...")
        
        # إنشاء المدير
        manager = SimpleHybridManager()
        
        # اختبار الوظائف الأساسية
        print("✅ تم إنشاء المدير بنجاح")
        
        # الحصول على Information النظام
        system_info = manager.get_system_status()
        print(f"📊 Information النظام: {system_info['system_name']}")
        
        # اختبار الاتصال بقاعدة البيانات
        db_info = manager.get_database_info()
        print(f"🗄️ قاعدة البيانات: {db_info.get('total_tables', 0)} جداول")
        
        # اختبار المزامنة
        sync_status = manager.get_sync_status()
        print(f"🔄 حالة المزامنة: {'Enabledة' if sync_status.get('sync_enabled') else 'Disabledة'}")
        
        print("✅ تم اختبار النظام بنجاح!")
        
    except Exception as e:
        print(f"❌ Error في اختبار النظام: {e}")
        import traceback
        traceback.print_exc()

