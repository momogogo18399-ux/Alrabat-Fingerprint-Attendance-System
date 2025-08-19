import os
import sqlite3
import datetime
from typing import Any, List, Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception:
    psycopg2 = None  # Optional when using SQLite only

DATABASE_FILE = os.getenv("SQLITE_FILE", "attendance.db")


class DatabaseManager:
    """
    طبقة وصول قاعدة البيانات بدعم مزدوج: SQLite (افتراضي) أو PostgreSQL عبر متغير البيئة DATABASE_URL.
    توحد أسلوب الاستعلامات وتعيد قواميس.
    """

    def __init__(self, db_file: str = DATABASE_FILE):
        self.database_url: Optional[str] = os.getenv("DATABASE_URL")
        self.is_postgres: bool = bool(self.database_url and self.database_url.startswith("postgres"))
        self.db_file = db_file
        print(f"[DB Manager] Using DATABASE_URL: {self.database_url}")
        if self.is_postgres:
            print("[DB Manager] Initialized for PostgreSQL via DATABASE_URL")
        else:
            print(f"[DB Manager] Initialized for local SQLite database: {self.db_file}")

    def _create_connection(self):
        """ينشئ ويعيد اتصالاً جديدًا بقاعدة البيانات (SQLite أو PostgreSQL)."""
        if self.is_postgres:
            if psycopg2 is None:
                print("psycopg2 not installed. Cannot connect to PostgreSQL.")
                return None
            print(f"[DB Manager] Attempting PostgreSQL connection...")
            try:
                conn = psycopg2.connect(self.database_url)
                print("[DB Manager] PostgreSQL connection successful.")
                return conn
            except Exception as e:
                print(f"PostgreSQL connection error: {e}")
                return None
        # SQLite
        try:
            conn = sqlite3.connect(self.db_file, timeout=15)
            conn.row_factory = sqlite3.Row
            try:
                conn.execute("PRAGMA foreign_keys = ON")
            except sqlite3.Error:
                pass
            return conn
        except sqlite3.Error as e:
            print(f"SQLite connection error: {e}")
            return None

    def _prepare_query(self, query: str) -> str:
        """تحويل صيغة البارامترات وعبارات خاصة لتوافق PostgreSQL عند الحاجة."""
        if not self.is_postgres:
            return query
        # استبدال placeholder من ? إلى %s
        rewritten = []
        q = query
        # أبسط تحويل: استبدال جميع ? بـ %s عندما لا تكون ضمن علامات
        # نفترض أن الاستعلامات لدينا بسيطة ولا تحتوي على ? حرفية
        rewritten_query = q.replace("?", "%s")

        # تحويل INSERT OR REPLACE في app_settings إلى UPSERT
        if "INSERT OR REPLACE INTO app_settings" in query:
            rewritten_query = (
                "INSERT INTO app_settings (key, value) VALUES (%s, %s) "
                "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value"
            )
        return rewritten_query

    def execute_query(self, query: str, params: tuple = (), fetchone: bool = False, fetchall: bool = False, commit: bool = False) -> Any:
        """ينفذ استعلام SQL ويدير الاتصال ويعيد قواميس عند الجلب."""
        conn = self._create_connection()
        if not conn:
            return None
        try:
            if self.is_postgres:
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                final_query = self._prepare_query(query)
            else:
                cursor = conn.cursor()
                final_query = query

            cursor.execute(final_query, params)
            if commit:
                conn.commit()
                try:
                    return cursor.lastrowid  # SQLite
                except Exception:
                    return None  # Postgres (بدون RETURNING)
            if fetchone:
                result = cursor.fetchone()
                return dict(result) if result else None
            if fetchall:
                results = cursor.fetchall()
                return [dict(row) for row in results] if results else []
        except Exception as e:
            print(f"Query failed: {e}\nQuery: {final_query}\nParams: {params}")
            return None
        finally:
            try:
                conn.close()
            except Exception:
                pass

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
        if self.is_postgres:
            conn = self._create_connection();
            if not conn: return None
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "INSERT INTO employees (employee_code, name, job_title, department, phone_number) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                        (data['employee_code'], data['name'], data['job_title'], data['department'], data['phone_number'])
                    )
                    conn.commit()
                    row = cur.fetchone()
                    return row['id'] if row else None
            finally:
                conn.close()
        query = "INSERT INTO employees (employee_code, name, job_title, department, phone_number) VALUES (?, ?, ?, ?, ?)"
        params = (data['employee_code'], data['name'], data['job_title'], data['department'], data['phone_number'])
        return self.execute_query(query, params, commit=True)
    
    def update_employee_qr_code(self, employee_id, qr_code):
        """تحديث رمز QR للموظف"""
        query = "UPDATE employees SET qr_code = ? WHERE id = ?"
        params = (qr_code, employee_id)
        return self.execute_query(query, params, commit=True)
    
    def get_employee_by_qr_code(self, qr_code):
        """البحث عن موظف برمز QR"""
        return self.execute_query("SELECT * FROM employees WHERE qr_code = ?", (qr_code,), fetchone=True)
    
    def get_attendance_by_employee_date(self, employee_id, date):
        """الحصول على تسجيل الحضور لموظف في تاريخ معين"""
        return self.execute_query(
            "SELECT * FROM attendance WHERE employee_id = ? AND date = ? ORDER BY check_time DESC LIMIT 1",
            (employee_id, date), fetchone=True
        )

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




       # --- دوال إدارة المواقع المعتمدة ---

    def add_location(self, data):
        """يضيف موقعًا معتمدًا جديدًا."""
        if self.is_postgres:
            conn = self._create_connection();
            if not conn: return None
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "INSERT INTO locations (name, latitude, longitude, radius_meters) VALUES (%s, %s, %s, %s) RETURNING id",
                        (data['name'], data['latitude'], data['longitude'], data['radius_meters'])
                    )
                    conn.commit(); row = cur.fetchone(); return row['id'] if row else None
            finally:
                conn.close()
        query = "INSERT INTO locations (name, latitude, longitude, radius_meters) VALUES (?, ?, ?, ?)"
        params = (data['name'], data['latitude'], data['longitude'], data['radius_meters'])
        return self.execute_query(query, params, commit=True)

    def get_all_locations(self):
        """يجلب كل المواقع المعتمدة."""
        return self.execute_query("SELECT * FROM locations ORDER BY name", fetchall=True)

    def update_location(self, data):
        """يحدّث بيانات موقع معتمد."""
        query = "UPDATE locations SET name = ?, latitude = ?, longitude = ?, radius_meters = ? WHERE id = ?"
        params = (data['name'], data['latitude'], data['longitude'], data['radius_meters'], data['id'])
        self.execute_query(query, params, commit=True)
        return True

    def delete_location(self, location_id):
        """يحذف موقعًا معتمدًا."""
        query = "DELETE FROM locations WHERE id = ?"
        self.execute_query(query, (location_id,), commit=True)
        return True



# في database_manager.py، داخل الكلاس

    def get_comprehensive_attendance_report(self, start_date, end_date):
        """
        ينشئ تقريرًا شاملاً ومجمعًا لكل الموظفين خلال فترة.
        """
        # هذا استعلام معقد يستخدم Common Table Expressions (WITH)
        query = """
        WITH DailyDurations AS (
            SELECT
                employee_id,
                date,
                SUM(work_duration_hours) as total_duration
            FROM attendance
            WHERE date BETWEEN ? AND ? AND type = 'Check-Out' AND work_duration_hours IS NOT NULL
            GROUP BY employee_id, date
        )
        SELECT 
            e.employee_code,
            e.name,
            COUNT(dd.date) AS attendance_days,
            ROUND(SUM(dd.total_duration), 2) AS total_work_hours,
            ROUND(AVG(dd.total_duration), 2) AS avg_daily_hours
        FROM employees e
        JOIN DailyDurations dd ON e.id = dd.employee_id
        GROUP BY e.id, e.employee_code, e.name
        ORDER BY e.name;
        """
        return self.execute_query(query, (start_date, end_date), fetchall=True)

    def get_employee_detailed_log(self, employee_id, start_date, end_date):
        """
        يجلب كل سجلات الحضور التفصيلية لموظف واحد خلال فترة.
        """
        query = """
        SELECT
            a.date,
            a.check_time,
            a.type,
            a.work_duration_hours,
            loc.name as location_name,
            a.notes
        FROM attendance a
        LEFT JOIN locations loc ON a.location_id = loc.id
        WHERE a.employee_id = ? AND a.date BETWEEN ? AND ?
        ORDER BY a.id ASC;
        """
        return self.execute_query(query, (employee_id, start_date, end_date), fetchall=True)
    




    # في database_manager.py

    def get_lateness_report(self, start_date, end_date, work_start_time_str, late_allowance_minutes):
        """
        ينشئ تقريرًا عن الموظفين المتأخرين خلال فترة محددة.
        
        :param start_date: تاريخ البدء (YYYY-MM-DD)
        :param end_date: تاريخ الانتهاء (YYYY-MM-DD)
        :param work_start_time_str: وقت بدء العمل الرسمي (HH:MM:SS)
        :param late_allowance_minutes: فترة السماح بالدقائق
        :return: قائمة بالموظفين المتأخرين مع تفاصيل التأخير.
        """
        # SQLite لا يدعم دوال الوقت المتقدمة مباشرة، لذلك سنقوم بالكثير من المعالجة في بايثون.
        # أولاً، نجلب كل سجلات الحضور الأولى لكل موظف في كل يوم.
        query = """
        SELECT 
            e.employee_code,
            e.name,
            a.date,
            MIN(a.check_time) as first_check_in
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        WHERE a.type = 'Check-In' AND a.date BETWEEN ? AND ?
        GROUP BY e.id, a.date
        ORDER BY e.name, a.date;
        """
        all_first_check_ins = self.execute_query(query, (start_date, end_date), fetchall=True)

        if not all_first_check_ins:
            return []

        # الآن، نقوم بفلترة هذه السجلات في بايثون لتحديد المتأخرين
        from datetime import datetime, timedelta

        work_start_time = datetime.strptime(work_start_time_str, "%H:%M:%S").time()
        deadline = (datetime.combine(datetime.min, work_start_time) + timedelta(minutes=late_allowance_minutes)).time()
        
        lateness_details = {} # قاموس لتجميع بيانات التأخير لكل موظف

        for record in all_first_check_ins:
            arrival_time = datetime.strptime(record['first_check_in'], "%H:%M:%S").time()

            if arrival_time > deadline:
                # هذا الموظف متأخر في هذا اليوم
                arrival_datetime = datetime.combine(datetime.min, arrival_time)
                deadline_datetime = datetime.combine(datetime.min, deadline)
                
                late_duration_seconds = (arrival_datetime - deadline_datetime).total_seconds()
                late_minutes = round(late_duration_seconds / 60)
                
                emp_code = record['employee_code']
                if emp_code not in lateness_details:
                    lateness_details[emp_code] = {
                        'employee_code': emp_code,
                        'name': record['name'],
                        'late_count': 0,
                        'total_late_minutes': 0,
                        'lateness_entries': []
                    }
                
                lateness_details[emp_code]['late_count'] += 1
                lateness_details[emp_code]['total_late_minutes'] += late_minutes
                lateness_details[emp_code]['lateness_entries'].append(f"{record['date']} ({late_minutes} min)")

        return list(lateness_details.values())
    



    def get_absence_report(self, start_date_str, end_date_str, work_days=[0, 1, 2, 3, 4]):
        """
        ينشئ تقريرًا عن غياب الموظفين، مع استبعاد الإجازات الرسمية.
        """
        from datetime import date, timedelta

        all_employees = self.get_all_employees()
        if not all_employees:
            return []

        attendance_records = self.execute_query(
            "SELECT DISTINCT employee_id, date FROM attendance WHERE date BETWEEN ? AND ?",
            (start_date_str, end_date_str), fetchall=True
        ) or []
        attendance_set = {(rec['employee_id'], rec['date']) for rec in attendance_records}

        holidays_records = self.get_all_holidays() or []
        holidays_set = {h['date'] for h in holidays_records}

        start_date, end_date = date.fromisoformat(start_date_str), date.fromisoformat(end_date_str)
        actual_work_dates = []
        current_date = start_date
        while current_date <= end_date:
            current_date_str = current_date.strftime("%Y-%m-%d")
            if current_date.weekday() in work_days and current_date_str not in holidays_set:
                actual_work_dates.append(current_date_str)
            current_date += timedelta(days=1)

        absence_report = []
        for emp in all_employees:
            absent_dates = [wd for wd in actual_work_dates if (emp['id'], wd) not in attendance_set]
            if absent_dates:
                absence_report.append({
                    'employee_code': emp['employee_code'],
                    'name': emp['name'],
                    'absence_count': len(absent_dates),
                    'absent_dates': ", ".join(absent_dates)
                })
        return absence_report

    def get_department_summary(self, start_date: str, end_date: str):
        """
        ملخص شهري مجمّع لكل قسم: عدد أيام الحضور وإجمالي ساعات العمل ومتوسطها.
        """
        query = """
        WITH CheckoutDurations AS (
            SELECT employee_id, date, work_duration_hours
            FROM attendance
            WHERE date BETWEEN ? AND ? AND type = 'Check-Out' AND work_duration_hours IS NOT NULL
        ),
        EmpDayAgg AS (
            SELECT e.department AS department,
                   cd.date AS date,
                   SUM(cd.work_duration_hours) AS total_hours
            FROM CheckoutDurations cd
            JOIN employees e ON e.id = cd.employee_id
            GROUP BY e.department, cd.date
        )
        SELECT department,
               COUNT(date) AS days_with_presence,
               ROUND(SUM(total_hours), 2) AS total_work_hours,
               ROUND(AVG(total_hours), 2) AS avg_daily_hours
        FROM EmpDayAgg
        GROUP BY department
        ORDER BY department;
        """
        return self.execute_query(query, (start_date, end_date), fetchall=True)

    def get_top_late_employees(self, start_date: str, end_date: str, work_start_time_str: str, late_allowance_minutes: int, top_n: int = 10):
        """
        يعيد أفضل المتأخرين تصنيفًا حسب إجمالي دقائق التأخر.
        """
        all_lateness = self.get_lateness_report(start_date, end_date, work_start_time_str, late_allowance_minutes) or []
        if not all_lateness:
            return []
        # ترتيب تنازليًا حسب إجمالي الدقائق
        all_lateness.sort(key=lambda r: r.get('total_late_minutes', 0), reverse=True)
        return all_lateness[:top_n]
    

    def get_overtime_report(self, start_date, end_date, standard_work_hours=8):
        """
        ينشئ تقريرًا عن ساعات العمل الإضافية للموظفين.
        
        :param start_date: تاريخ البدء
        :param end_date: تاريخ الانتهاء
        :param standard_work_hours: عدد ساعات العمل الرسمية في اليوم
        :return: قائمة بسجلات العمل الإضافي.
        """
        # هذا الاستعلام يجلب كل أيام العمل التي تجاوزت المدة الرسمية
        query = """
        SELECT
            e.employee_code,
            e.name,
            a.date,
            a.work_duration_hours,
            (a.work_duration_hours - ?) AS overtime_hours
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        WHERE 
            a.type = 'Check-Out' AND
            a.date BETWEEN ? AND ? AND
            a.work_duration_hours > ?
        ORDER BY e.name, a.date;
        """
        # لاحظ أننا نمرر standard_work_hours مرتين في البارامترات
        params = (standard_work_hours, start_date, end_date, standard_work_hours)
        
        overtime_records = self.execute_query(query, params, fetchall=True)
        return overtime_records if overtime_records else []
    

    




        # --- دوال إدارة الإجازات ---

    def add_holiday(self, date_str, description):
        """يضيف يوم إجازة رسمي جديد."""
        if self.is_postgres:
            conn = self._create_connection();
            if not conn: return None
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "INSERT INTO holidays (date, description) VALUES (%s, %s) RETURNING id",
                        (date_str, description)
                    )
                    conn.commit(); row = cur.fetchone(); return row['id'] if row else None
            finally:
                conn.close()
        query = "INSERT INTO holidays (date, description) VALUES (?, ?)"
        return self.execute_query(query, (date_str, description), commit=True)

    def get_all_holidays(self):
        """يجلب كل الإجازات الرسمية مرتبة بالتاريخ."""
        return self.execute_query("SELECT * FROM holidays ORDER BY date DESC", fetchall=True)

    def delete_holiday(self, holiday_id):
        """يحذف يوم إجازة رسمي."""
        query = "DELETE FROM holidays WHERE id = ?"
        self.execute_query(query, (holiday_id,), commit=True)
        return True



        

    # --- تعديل دالة إضافة سجل الحضور ---
    def add_attendance_record(self, data):
        """يضيف سجل حضور جديد (مع location_id)."""
        if self.is_postgres:
            conn = self._create_connection();
            if not conn: return None
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        """
                        INSERT INTO attendance (employee_id, check_time, date, type, location_id, notes)
                        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
                        """,
                        (data['employee_id'], data['check_time'], data['date'], data['type'], data.get('location_id'), data.get('notes'))
                    )
                    conn.commit(); row = cur.fetchone(); return row['id'] if row else None
            finally:
                conn.close()
        query = "INSERT INTO attendance (employee_id, check_time, date, type, location_id, notes) VALUES (?, ?, ?, ?, ?, ?)"
        params = (data['employee_id'], data['check_time'], data['date'], data['type'], data.get('location_id'), data.get('notes'))
        return self.execute_query(query, params, commit=True)
    
    def add_attendance(self, data):
        """دالة مختصرة لإضافة سجل حضور (لتوافق مع QR Scanner)"""
        return self.add_attendance_record(data)
    


    def get_attendance_by_date(self, target_date: str):
        """
        يجلب جميع سجلات الحضور لتاريخ محدد، مع التأكد من جلب location_id.
        """
        # --- بداية التصحيح الحاسم ---
        query = """
        SELECT 
            a.id, 
            a.employee_id, 
            e.name AS employee_name, 
            a.check_time, 
            a.type,
            a.location_id, --  <-- هذا هو السطر الذي كان ناقصًا
            loc.name AS location_name,
            a.work_duration_hours, 
            a.notes
        FROM attendance a
        JOIN employees e ON a.employee_id = e.id
        LEFT JOIN locations loc ON a.location_id = loc.id
        WHERE a.date = ? 
        ORDER BY a.id
        """
        # --- نهاية التصحيح الحاسم ---
        return self.execute_query(query, (target_date,), fetchall=True)
        

    # --- بداية التعديل الحاسم ---
    def get_last_action_today(self, employee_id, date_str):
        """
        يجلب آخر إجراء (Check-In/Check-Out) لموظف في يوم محدد.
        يعيد سلسلة نصية ('Check-In' أو 'Check-Out') أو None.
        """
        query = "SELECT type FROM attendance WHERE employee_id = ? AND date = ? ORDER BY id DESC LIMIT 1"
        result = self.execute_query(query, (employee_id, date_str), fetchone=True)
        return result['type'] if result else None
    # --- نهاية التعديل الحاسم ---
    
    def get_check_in_time_today(self, employee_id, date_str):
        """
        يجلب أول وقت تسجيل دخول لموظف في يوم محدد.
        يعيد سلسلة نصية (HH:MM:SS) أو None.
        """
        query = "SELECT check_time FROM attendance WHERE employee_id = ? AND date = ? AND type = 'Check-In' ORDER BY id ASC LIMIT 1"
        result = self.execute_query(query, (employee_id, date_str), fetchone=True)
        return result['check_time'] if result else None

    def update_checkout_with_duration(self, record_id, duration_hours):
        self.execute_query("UPDATE attendance SET work_duration_hours = ? WHERE id = ?", (duration_hours, record_id), commit=True)

    def get_employee_attendance_history(self, employee_id):
        return self.execute_query("SELECT date, check_time, type, notes FROM attendance WHERE employee_id = ? ORDER BY id DESC", (employee_id,), fetchall=True)

    def get_attendance_between_dates(self, start_date, end_date):
        return self.execute_query("SELECT * FROM attendance WHERE date BETWEEN ? AND ?", (start_date, end_date), fetchall=True)

    # --- دوال إدارة المستخدمين والإعدادات ---
    def get_user_by_username(self, username: str):
        return self.execute_query('SELECT * FROM "users" WHERE username = ?', (username,), fetchone=True)
        
    def get_all_users(self):
        return self.execute_query('SELECT id, username, role FROM "users"', fetchall=True)

    def add_user(self, username, hashed_password, role):
        """يضيف مستخدماً جديداً ويعيد المعرف. يرجع None إذا كان الاسم موجوداً بالفعل."""
        # تحقق مسبق من التكرار لتقديم رسالة أدق
        existing = self.execute_query('SELECT id FROM "users" WHERE username = ?', (username,), fetchone=True)
        if existing:
            return None
        return self.execute_query('INSERT INTO "users" (username, password, role) VALUES (?, ?, ?)', (username, hashed_password, role), commit=True)

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
        self.execute_query("INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)", (key, value), commit=True)


    # --- دوال إدارة جلسات المشرفين ---
    def create_admin_session(self, user_id: int, token: str) -> bool:
        """إنشاء جلسة مشرف جديدة في قاعدة البيانات."""
        query = "INSERT INTO admin_sessions (user_id, token) VALUES (?, ?)"
        # لتجنب التعقيد، سنقوم بحذف الجلسات القديمة للمستخدم قبل إنشاء واحدة جديدة
        self.execute_query("DELETE FROM admin_sessions WHERE user_id = ?", (user_id,), commit=True)
        self.execute_query(query, (user_id, token), commit=True)
        return True

    def validate_admin_session(self, token: str) -> Optional[dict]:
        """التحقق من صلاحية جلسة المشرف وإرجاع بيانات المستخدم إذا كانت صالحة."""
        # حذف الجلسات التي مضى عليها أكثر من ساعة واحدة
        if self.is_postgres:
            self.execute_query("DELETE FROM admin_sessions WHERE created_at < NOW() - INTERVAL '1 hour'", commit=True)
        else:
            # SQLite
            self.execute_query("DELETE FROM admin_sessions WHERE created_at < DATETIME('now', '-1 hour')", commit=True)
        
        query = """
            SELECT u.id, u.username, u.role 
            FROM admin_sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
        """
        return self.execute_query(query, (token,), fetchone=True)


