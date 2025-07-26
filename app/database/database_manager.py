import os
import datetime
import psycopg2
from psycopg2.extras import RealDictCursor

class DatabaseManager:
    """
    يعالج جميع عمليات قاعدة البيانات للتطبيق، مع دعم PostgreSQL.
    """
    def __init__(self, db_url=None):
        """
        يقوم بالتهيئة باستخدام عنوان URL للاتصال بقاعدة بيانات PostgreSQL.
        إذا لم يتم توفير عنوان URL، فإنه يفترض بيئة تطوير محلية (SQLite).
        """
        self.db_url = db_url
        self.is_postgres = self.db_url and self.db_url.startswith("postgres")

        if not self.is_postgres:
            # إعدادات SQLite للتطوير المحلي
            self.db_file = "attendance.db"
            print("[DB Manager] Initialized in SQLite mode.")
        else:
            print("[DB Manager] Initialized in PostgreSQL mode.")

    def _create_connection(self):
        """ينشئ ويعيد اتصالاً جديدًا بقاعدة البيانات."""
        if self.is_postgres:
            try:
                return psycopg2.connect(self.db_url)
            except psycopg2.OperationalError as e:
                print(f"PostgreSQL connection error: {e}")
                return None
        else: # وضع SQLite
            import sqlite3
            try:
                conn = sqlite3.connect(self.db_file, timeout=15)
                conn.row_factory = sqlite3.Row
                return conn
            except sqlite3.Error as e:
                print(f"SQLite connection error: {e}")
                return None
    
    def execute_query(self, query, params=(), fetchone=False, fetchall=False, commit=False):
        """
        ينفذ استعلام SQL ويدير الاتصال، مع دعم مزدوج لـ SQLite و PostgreSQL.
        """
        conn = self._create_connection()
        if not conn: return None
        
        last_id = None
        
        # تحويل صيغة الاستعلام لـ PostgreSQL إذا لزم الأمر
        if self.is_postgres:
            query = query.replace('?', '%s')
            
        try:
            if self.is_postgres:
                # استخدام RealDictCursor يجعل النتائج كقواميس في PostgreSQL
                cursor = conn.cursor(cursor_factory=RealDictCursor)
            else:
                cursor = conn.cursor()

            cursor.execute(query, params)
            
            if 'RETURNING id' in query.upper() and cursor.rowcount > 0:
                last_id = cursor.fetchone()['id']

            if commit:
                conn.commit()
                # في SQLite، نحصل على lastrowid بشكل مختلف
                return last_id if self.is_postgres else cursor.lastrowid
            
            if fetchone:
                result = cursor.fetchone()
                return dict(result) if result else None
            
            if fetchall:
                results = cursor.fetchall()
                return [dict(row) for row in results] if results else []

        except Exception as e:
            print(f"Query failed: {e}\nQuery: {query}\nParams: {params}")
            if conn: conn.rollback()
            return None
        finally:
            if conn:
                conn.close()

    # --- دوال إدارة الموظفين ---
    def get_all_employees(self):
        return self.execute_query("SELECT * FROM employees ORDER BY name", fetchall=True)

    def get_employee_by_id(self, employee_id):
        return self.execute_query("SELECT * FROM employees WHERE id = ?", (employee_id,), fetchone=True)
        
    def get_employee_by_code(self, employee_code):
        return self.execute_query("SELECT * FROM employees WHERE employee_code = ?", (employee_code,), fetchone=True)

    def get_employee_by_phone(self, phone_number):
        return self.execute_query("SELECT * FROM employees WHERE phone_number = ?", (phone_number,), fetchone=True)

    def get_employee_by_token(self, token):
        return self.execute_query("SELECT * FROM employees WHERE device_token = ?", (token,), fetchone=True)
        
    def get_employee_by_fingerprint(self, fingerprint):
        return self.execute_query("SELECT * FROM employees WHERE web_fingerprint = ?", (fingerprint,), fetchone=True)

    def add_employee(self, data):
        query = "INSERT INTO employees (employee_code, name, job_title, department, phone_number) VALUES (?, ?, ?, ?, ?) RETURNING id;"
        params = (data['employee_code'], data['name'], data['job_title'], data['department'], data['phone_number'])
        return self.execute_query(query, params, commit=True)

    def update_employee(self, data):
        query = "UPDATE employees SET employee_code = ?, name = ?, job_title = ?, department = ?, phone_number = ? WHERE id = ?"
        params = (data['employee_code'], data['name'], data['job_title'], data['department'], data['phone_number'], data['id'])
        self.execute_query(query, params, commit=True); return True

    def delete_employee(self, employee_id):
        self.execute_query("DELETE FROM employees WHERE id = ?", (employee_id,), commit=True); return True
        
    def update_employee_device_info(self, employee_id, fingerprint, token):
        self.execute_query("UPDATE employees SET web_fingerprint = ?, device_token = ? WHERE id = ?", (fingerprint, token, employee_id), commit=True)
        
    def update_employee_zk_template(self, employee_id, zk_template):
        self.execute_query("UPDATE employees SET zk_template = ? WHERE id = ?", (zk_template, employee_id), commit=True)
    
    def reset_employee_device_info(self, employee_id):
        self.execute_query("UPDATE employees SET web_fingerprint = NULL, device_token = NULL WHERE id = ?", (employee_id,), commit=True); return True
        
    def search_employees(self, search_term):
        term = f"%{search_term}%"
        return self.execute_query("SELECT * FROM employees WHERE name LIKE ? OR phone_number LIKE ? OR employee_code LIKE ?", (term, term, term), fetchall=True)

    # --- دوال إدارة الحضور ---
    def add_attendance_record(self, data):
        query = "INSERT INTO attendance (employee_id, check_time, date, type, location_lat, location_lon, notes) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id;"
        params = (data['employee_id'], data['check_time'], data['date'], data['type'], data.get('lat'), data.get('lon'), data.get('notes'))
        return self.execute_query(query, params, commit=True)

    def get_attendance_by_date(self, target_date: str):
        query = """
        SELECT a.id, a.employee_id, e.name, a.check_time, a.type, a.location_lat, 
               a.location_lon, a.work_duration_hours, a.notes
        FROM attendance a JOIN employees e ON a.employee_id = e.id
        WHERE a.date = ? ORDER BY a.id
        """
        return self.execute_query(query, (target_date,), fetchall=True)

    def get_last_action_today(self, employee_id, date_str):
        result = self.execute_query("SELECT type FROM attendance WHERE employee_id = ? AND date = ? ORDER BY id DESC LIMIT 1", (employee_id, date_str), fetchone=True)
        return result['type'] if result else None
    
    def get_check_in_time_today(self, employee_id, date_str):
        result = self.execute_query("SELECT check_time FROM attendance WHERE employee_id = ? AND date = ? AND type = 'Check-In' ORDER BY id ASC LIMIT 1", (employee_id, date_str), fetchone=True)
        return result['check_time'] if result else None

    def update_checkout_with_duration(self, record_id, duration_hours):
        self.execute_query("UPDATE attendance SET work_duration_hours = ? WHERE id = ?", (duration_hours, record_id), commit=True)

    def get_employee_attendance_history(self, employee_id):
        return self.execute_query("SELECT date, check_time, type, notes FROM attendance WHERE employee_id = ? ORDER BY id DESC", (employee_id,), fetchall=True)

    # --- دوال إدارة المستخدمين والإعدادات ---
    def get_user_by_username(self, username: str):
        return self.execute_query('SELECT * FROM "users" WHERE username = ?', (username,), fetchone=True)
        
    def get_all_users(self):
        return self.execute_query('SELECT id, username, role FROM "users"', fetchall=True)

    def add_user(self, username, hashed_password, role):
        query = 'INSERT INTO "users" (username, password, role) VALUES (?, ?, ?) RETURNING id;'
        return self.execute_query(query, (username, hashed_password, role), commit=True)

    def update_user_password(self, user_id, hashed_password):
        self.execute_query('UPDATE "users" SET password = ? WHERE id = ?', (hashed_password, user_id), commit=True); return True

    def update_user_role(self, user_id, new_role):
        self.execute_query('UPDATE "users" SET role = ? WHERE id = ?', (new_role, user_id), commit=True); return True

    def delete_user(self, user_id):
        if user_id == 1: return False
        self.execute_query('DELETE FROM "users" WHERE id = ?', (user_id,), commit=True); return True

    def get_all_settings(self):
        rows = self.execute_query("SELECT key, value FROM app_settings", fetchall=True)
        return {row['key']: row['value'] for row in rows} if rows else {}

    def save_setting(self, key, value):
        if self.is_postgres:
            query = "INSERT INTO app_settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;"
            self.execute_query(query, (key, value), commit=True)
        else:
            query = "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)"
            self.execute_query(query, (key, value), commit=True)