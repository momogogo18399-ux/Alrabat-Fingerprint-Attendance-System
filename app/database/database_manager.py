import os
import sqlite3
import logging
from datetime import datetime
import hashlib
from typing import Any, List, Optional, Dict

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except Exception:
    psycopg2 = None  # Optional when using SQLite only

DATABASE_FILE = os.getenv("SQLITE_FILE", "attendance.db")


class DatabaseManager:
    """
    Database access layer with dual support: SQLite (default) or PostgreSQL via DATABASE_URL environment variable.
    Unifies query style and returns dictionaries.
    """

    def __init__(self):
        # Database settings
        self.database_url: Optional[str] = None  # Disable DATABASE_URL
        
        # Force local system usage
        force_local = os.getenv('FORCE_LOCAL_DATABASE', 'true').lower() == 'true'
        use_sqlite_only = os.getenv('USE_SQLITE_ONLY', 'true').lower() == 'true'
        
        if force_local or use_sqlite_only:
            self.database_url = None
            print("[DB Manager] Forced to use LOCAL SQLite database")
        else:
            self.database_url = os.getenv("DATABASE_URL")
        
        self.sqlite_file = os.getenv("SQLITE_FILE", "attendance.db")
        self.database_file = os.path.join(os.path.dirname(__file__), "..", "..", self.sqlite_file)
        
        # Determine database type
        if self.database_url and not force_local:
            self.db_type = "postgresql"
            print(f"[DB Manager] Initialized for PostgreSQL via DATABASE_URL")
        else:
            self.db_type = "sqlite"
            print(f"[DB Manager] Initialized for LOCAL SQLite: {self.database_file}")
        
        # Initialize database
        self._init_database()

    def _create_connection(self):
        """Create database connection"""
        if self.db_type == "postgresql" and self.database_url:
            try:
                import psycopg2
                return psycopg2.connect(self.database_url)
            except ImportError:
                print("[DB Manager] psycopg2 not installed, falling back to SQLite")
                self.db_type = "sqlite"
            except Exception as e:
                print(f"[DB Manager] PostgreSQL connection failed: {e}, falling back to SQLite")
                self.db_type = "sqlite"
        
        # Use SQLite as default option
        try:
            return sqlite3.connect(self.database_file)
        except Exception as e:
            print(f"[DB Manager] SQLite connection failed: {e}")
            raise
    
    def _init_database(self):
        """Initialize database"""
        try:
            if self.db_type == "sqlite":
                # Ensure local database exists
                if not os.path.exists(self.database_file):
                    print(f"[DB Manager] Creating new local SQLite database: {self.database_file}")
                    self._create_sqlite_tables()
                else:
                    print(f"[DB Manager] Using existing local SQLite database: {self.database_file}")
            else:
                print(f"[DB Manager] Using PostgreSQL database")
        except Exception as e:
            print(f"[DB Manager] Database initialization error: {e}")
            # Fallback to SQLite
            self.db_type = "sqlite"
            self._init_database()
    
    def _create_sqlite_tables(self):
        """Create SQLite tables"""
        try:
            conn = sqlite3.connect(self.database_file)
            cursor = conn.cursor()
            
            # Create basic tables
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS employees (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_code TEXT UNIQUE,
                    name TEXT NOT NULL,
                    job_title TEXT,
                    department TEXT,
                    phone_number TEXT UNIQUE,
                    qr_code TEXT,
                    web_fingerprint TEXT,
                    device_token TEXT,
                    zk_template TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id TEXT,
                    employee_name TEXT,
                    check_time TIMESTAMP,
                    date DATE,
                    type TEXT,
                    location_id INTEGER,
                    notes TEXT,
                    work_duration_hours REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT DEFAULT 'user',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    latitude REAL,
                    longitude REAL,
                    radius_meters REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS holidays (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    token TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
            print("[DB Manager] SQLite tables created successfully")
            
        except Exception as e:
            print(f"[DB Manager] Error creating SQLite tables: {e}")
            raise

    def _prepare_query(self, query: str) -> str:
        """Prepare query based on database type"""
        if self.db_type == "postgresql":
            # Convert SQLite to PostgreSQL
            return query.replace("?", "%s")
        else:
            # SQLite
            return query
    
    def _execute_query(self, query: str, params: tuple = None, fetch: bool = True):
        """Execute query on database"""
        conn = None
        try:
            conn = self._create_connection()
            if conn is None:
                return None
            
            cursor = conn.cursor()
            
            # Prepare query
            prepared_query = self._prepare_query(query)
            
            if params:
                cursor.execute(prepared_query, params)
            else:
                cursor.execute(prepared_query)
            
            if fetch:
                if query.strip().upper().startswith("SELECT"):
                    result = cursor.fetchall()
                    # Convert results to dictionaries
                    if result and self.db_type == "sqlite":
                        columns = [description[0] for description in cursor.description]
                        return [dict(zip(columns, row)) for row in result]
                    return result
                else:
                    conn.commit()
                    return cursor.rowcount
            
            conn.commit()
            return True
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"[DB Manager] Query execution error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def _execute_query_with_commit(self, query: str, params: tuple = None):
        """Execute query with commit - for operations that need commit"""
        conn = None
        try:
            conn = self._create_connection()
            if conn is None:
                return None
            
            cursor = conn.cursor()
            
            # Prepare query
            prepared_query = self._prepare_query(query)
            
            if params:
                cursor.execute(prepared_query, params)
            else:
                cursor.execute(prepared_query)

            conn.commit()
            
            # Return inserted record ID (for INSERT operations)
            if query.strip().upper().startswith("INSERT"):
                return cursor.lastrowid
            
            return cursor.rowcount
            
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"[DB Manager] Query execution error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    # --- Employee Management Functions ---
    def get_all_employees(self):
        return self._execute_query("SELECT * FROM employees ORDER BY name", fetch=True)

    def get_employee_by_id(self, employee_id):
        """Get single employee by ID"""
        result = self._execute_query("SELECT * FROM employees WHERE id = ?", (employee_id,), fetch=True)
        if result and isinstance(result, list) and len(result) > 0:
            return result[0]
        elif result and isinstance(result, dict):
            return result
        return None
        
    def get_employee_by_code(self, employee_code):
        """Get single employee by code"""
        result = self._execute_query("SELECT * FROM employees WHERE employee_code = ?", (employee_code,), fetch=True)
        if result and isinstance(result, list) and len(result) > 0:
            return result[0]
        elif result and isinstance(result, dict):
            return result
        return None

    def get_employee_by_phone(self, phone_number):
        """Get single employee by phone number"""
        result = self._execute_query("SELECT * FROM employees WHERE phone_number = ?", (phone_number,), fetch=True)
        if result and isinstance(result, list) and len(result) > 0:
            return result[0]
        elif result and isinstance(result, dict):
            return result
        return None

    def get_employee_by_token(self, token):
        """Get single employee by device token"""
        result = self._execute_query("SELECT * FROM employees WHERE device_token = ?", (token,), fetch=True)
        if result and isinstance(result, list) and len(result) > 0:
            return result[0]
        elif result and isinstance(result, dict):
            return result
        return None
        
    def get_employee_by_fingerprint(self, fingerprint):
        """Get single employee by fingerprint"""
        result = self._execute_query("SELECT * FROM employees WHERE web_fingerprint = ?", (fingerprint,), fetch=True)
        if result and isinstance(result, list) and len(result) > 0:
            return result[0]
        elif result and isinstance(result, dict):
            return result
        return None

    def add_employee(self, data):
        """Add new employee"""
        if self.db_type == "postgresql":
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
        
        # SQLite
        query = "INSERT INTO employees (employee_code, name, job_title, department, phone_number) VALUES (?, ?, ?, ?, ?)"
        params = (data['employee_code'], data['name'], data['job_title'], data['department'], data['phone_number'])
        return self._execute_query_with_commit(query, params)
    
    def update_employee_qr_code(self, employee_id, qr_code):
        """Update employee QR code"""
        query = "UPDATE employees SET qr_code = ? WHERE id = ?"
        params = (qr_code, employee_id)
        return self._execute_query_with_commit(query, params)
    
    def get_employee_by_qr_code(self, qr_code):
        """Search for employee by QR code"""
        result = self._execute_query("SELECT * FROM employees WHERE qr_code = ?", (qr_code,), fetch=True)
        if result and isinstance(result, list) and len(result) > 0:
            return result[0]
        elif result and isinstance(result, dict):
            return result
        return None
    
    def get_attendance_by_employee_date(self, employee_id, date):
        """Get attendance record for employee on specific date"""
        result = self._execute_query(
            "SELECT * FROM attendance WHERE employee_id = ? AND date = ? ORDER BY check_time DESC LIMIT 1",
            (employee_id, date), fetch=True
        )
        if result and isinstance(result, list) and len(result) > 0:
            return result[0]
        elif result and isinstance(result, dict):
            return result
        return None

    def update_employee(self, employee_id: str, employee_data: Dict[str, Any]) -> bool:
        """Update employee"""
        try:
            query = """
                UPDATE employees SET 
                    employee_code = ?, name = ?, department = ?, job_title = ?, qr_code = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """
            params = (
                employee_data.get('employee_code'), employee_data.get('name'), 
                employee_data.get('department'), employee_data.get('job_title'), 
                employee_data.get('qr_code'), employee_id
            )
            return self._execute_query_with_commit(query, params)
        except Exception as e:
            print(f"[DB Manager] Error updating employee: {e}")
            return False

    def delete_employee(self, employee_id):
        return self._execute_query_with_commit("DELETE FROM employees WHERE id = ?", (employee_id,))
        
    def update_employee_device_info(self, employee_id, fingerprint, token):
        return self._execute_query_with_commit("UPDATE employees SET web_fingerprint = ?, device_token = ? WHERE id = ?", (fingerprint, token, employee_id))
        
    def update_employee_zk_template(self, employee_id, zk_template):
        return self._execute_query_with_commit("UPDATE employees SET zk_template = ? WHERE id = ?", (zk_template, employee_id))
    
    def reset_employee_device_info(self, employee_id):
        return self._execute_query_with_commit("UPDATE employees SET web_fingerprint = NULL, device_token = NULL WHERE id = ?", (employee_id,))
        
    def search_employees(self, search_term):
        term = f"%{search_term}%"
        return self._execute_query("SELECT * FROM employees WHERE name LIKE ? OR phone_number LIKE ? OR employee_code LIKE ?", (term, term, term), fetch=True)




       # --- دوال إدارة المواقع المعتمدة ---

    def add_location(self, data):
        """يضيف موقعًا معتمدًا جديدًا."""
        if self.db_type == "postgresql":
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
        return self._execute_query_with_commit(query, params)

    def get_all_locations(self):
        """يجلب كل المواقع المعتمدة."""
        return self._execute_query("SELECT * FROM locations ORDER BY name", fetch=True)

    def update_location(self, data):
        """يحدّث بيانات موقع معتمد."""
        query = "UPDATE locations SET name = ?, latitude = ?, longitude = ?, radius_meters = ? WHERE id = ?"
        params = (data['name'], data['latitude'], data['longitude'], data['radius_meters'], data['id'])
        return self._execute_query_with_commit(query, params)

    def delete_location(self, location_id):
        """يDelete موقعًا معتمدًا."""
        query = "DELETE FROM locations WHERE id = ?"
        return self._execute_query_with_commit(query, (location_id,))



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
        return self._execute_query(query, (start_date, end_date), fetch=True)

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
        return self._execute_query(query, (employee_id, start_date, end_date), fetch=True)
    




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
        all_first_check_ins = self._execute_query(query, (start_date, end_date), fetch=True)

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

        attendance_records = self._execute_query(
            "SELECT DISTINCT employee_id, date FROM attendance WHERE date BETWEEN ? AND ?",
            (start_date_str, end_date_str), fetch=True
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
        return self._execute_query(query, (start_date, end_date), fetch=True)

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
        
        overtime_records = self._execute_query(query, params, fetch=True)
        return overtime_records if overtime_records else []
    

    




        # --- دوال إدارة الإجازات ---

    def add_holiday(self, date_str, description):
        """يضيف يوم إجازة رسمي جديد."""
        if self.db_type == "postgresql":
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
        return self._execute_query_with_commit(query, (date_str, description))

    def get_all_holidays(self):
        """يجلب كل الإجازات الرسمية مرتبة بالتاريخ."""
        return self._execute_query("SELECT * FROM holidays ORDER BY date DESC", fetch=True)

    def delete_holiday(self, holiday_id):
        """يDelete يوم إجازة رسمي."""
        query = "DELETE FROM holidays WHERE id = ?"
        return self._execute_query_with_commit(query, (holiday_id,))



        

    # --- Edit دالة Add سجل الحضور ---
    def add_attendance_record(self, data):
        """يضيف سجل حضور جديد (مع location_id)."""
        if self.db_type == "postgresql":
            conn = self._create_connection();
            if not conn: return None
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute(
                        "INSERT INTO attendance (employee_id, check_time, date, type, location_id, notes) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
                        (data['employee_id'], data['check_time'], data['date'], data['type'], data.get('location_id'), data.get('notes'))
                    )
                    conn.commit()
                    row = cur.fetchone()
                    return row['id'] if row else None
            finally:
                conn.close()
        
        # SQLite
        query = "INSERT INTO attendance (employee_id, check_time, date, type, location_id, notes) VALUES (?, ?, ?, ?, ?, ?)"
        params = (data['employee_id'], data['check_time'], data['date'], data['type'], data.get('location_id'), data.get('notes'))
        return self._execute_query_with_commit(query, params)
    
    def add_attendance(self, data):
        """دالة مختصرة لAdd سجل حضور (لتوافق مع QR Scanner)"""
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
        return self._execute_query(query, (target_date,), fetch=True)
        

    # --- بداية الEdit الحاسم ---
    def get_last_action_today(self, employee_id, date_str):
        """
        يجلب آخر إجراء (Check-In/Check-Out) لموظف في يوم محدد.
        يعيد سلسلة نصية ('Check-In' أو 'Check-Out') أو None.
        """
        result = self._execute_query("SELECT type FROM attendance WHERE employee_id = ? AND date = ? ORDER BY id DESC LIMIT 1", (employee_id, date_str), fetch=True)
        if result and isinstance(result, list) and len(result) > 0:
            return result[0].get('type')
        elif result and isinstance(result, dict):
            return result.get('type')
        return None
    # --- نهاية الEdit الحاسم ---
    
    def get_first_check_in_time(self, employee_id: str, date_str: str) -> Optional[str]:
        query = "SELECT check_time FROM attendance WHERE employee_id = ? AND date = ? AND type = 'Check-In' ORDER BY id ASC LIMIT 1"
        result = self._execute_query(query, (employee_id, date_str), fetch=True)
        if result and isinstance(result, list) and len(result) > 0:
            return result[0].get('check_time')
        elif result and isinstance(result, dict):
            return result.get('check_time')
        return None

    def update_checkout_with_duration(self, record_id, duration_hours):
        return self._execute_query_with_commit("UPDATE attendance SET work_duration_hours = ? WHERE id = ?", (duration_hours, record_id))

    def get_employee_attendance_history(self, employee_id):
        return self._execute_query("SELECT date, check_time, type, notes FROM attendance WHERE employee_id = ? ORDER BY id DESC", (employee_id,), fetch=True)

    def get_attendance_between_dates(self, start_date, end_date):
        return self._execute_query("SELECT * FROM attendance WHERE date BETWEEN ? AND ?", (start_date, end_date), fetch=True)

    # --- دوال إدارة المستخدمين والإعدادات ---
    def get_user_by_username(self, username: str):
        """يجلب مستخدماً واحداً بالاسم"""
        result = self._execute_query('SELECT * FROM "users" WHERE username = ?', (username,), fetch=True)
        # التأكد من إرجاع قاموس واحد بدلاً من قائمة
        if result and isinstance(result, list) and len(result) > 0:
            return result[0]  # إرجاع العنصر الأول فقط
        elif result and isinstance(result, dict):
            return result
        return None
        
    def get_all_users(self):
        return self._execute_query('SELECT id, username, role FROM "users"', fetch=True)

    def add_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add مستخدم"""
        try:
            if isinstance(user_data, dict):
                username = user_data.get('username')
                password = user_data.get('password', 'default123')
                role = user_data.get('role', 'user')
            else:
                username = user_data
                password = 'default123'
                role = 'user'
            
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            user_id = self._execute_query_with_commit('INSERT INTO "users" (username, password, role) VALUES (?, ?, ?)', (username, hashed_password, role))
            
            if user_id:
                return {
                    'id': user_id,
                    'username': username,
                    'role': role
                }
            return None
            
        except Exception as e:
            print(f"[DB Manager] Error adding user: {e}")
            return None

    def update_user_password(self, user_id, hashed_password):
        return self._execute_query_with_commit('UPDATE "users" SET password = ? WHERE id = ?', (hashed_password, user_id))

    def update_user_role(self, user_id, new_role):
        return self._execute_query_with_commit('UPDATE "users" SET role = ? WHERE id = ?', (new_role, user_id))

    def delete_user(self, user_id):
        if user_id == 1: return False
        return self._execute_query_with_commit('DELETE FROM "users" WHERE id = ?', (user_id,))

    def get_all_settings(self):
        rows = self._execute_query("SELECT key, value FROM app_settings", fetch=True)
        return {row['key']: row['value'] for row in rows} if rows else {}

    def save_setting(self, key, value):
        return self._execute_query_with_commit("INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)", (key, value))


    # --- دوال إدارة جلسات المشرفين ---
    def create_admin_session(self, user_id: int, token: str) -> bool:
        """إنشاء جلسة مشرف جديدة في قاعدة البيانات."""
        query = "INSERT INTO admin_sessions (user_id, token) VALUES (?, ?)"
        # لتجنب التعقيد، سنقوم بDelete الجلسات القديمة للمستخدم قبل إنشاء واحدة جديدة
        self._execute_query_with_commit("DELETE FROM admin_sessions WHERE user_id = ?", (user_id,))
        return self._execute_query_with_commit(query, (user_id, token))

    def validate_admin_session(self, token: str) -> Optional[dict]:
        """التحقق من صلاحية جلسة المشرف وإرجاع بيانات المستخدم إذا كانت صالحة."""
        # Delete الجلسات التي مضى عليها أكثر من ساعة واحدة
        if self.db_type == "postgresql":
            self._execute_query_with_commit("DELETE FROM admin_sessions WHERE created_at < NOW() - INTERVAL '1 hour'")
        else:
            # SQLite
            self._execute_query_with_commit("DELETE FROM admin_sessions WHERE created_at < DATETIME('now', '-1 hour')")
        
        query = """
            SELECT u.id, u.username, u.role 
            FROM admin_sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.token = ?
        """
        result = self._execute_query(query, (token,), fetch=True)
        if result and isinstance(result, list) and len(result) > 0:
            return result[0]
        elif result and isinstance(result, dict):
            return result
        return None

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """مصادقة المستخدم"""
        try:
            user = self.get_user_by_username(username)
            if user and self._verify_password(password, user.get('password', '')):
                return user
            return None
        except Exception as e:
            print(f"[DB Manager] Authentication error: {e}")
            return None
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """التحقق من كلمة المرور"""
        try:
            import hashlib
            return hashlib.sha256(password.encode()).hexdigest() == hashed
        except Exception:
            return False
    
    def setup_default_data(self):
        """إعداد البيانات الافتراضية"""
        try:
            # Add مستخدم افتراضي
            admin_password = hashlib.sha256("admin123".encode()).hexdigest()
            # Check if admin user already exists
            if not self.get_user_by_username("admin"):
                self._execute_query_with_commit('INSERT INTO "users" (username, password, role) VALUES (?, ?, ?)', ("admin", admin_password, "admin"))
            
            # Add إعدادات افتراضية
            default_settings = {
                'theme': 'light',
                'language': 'ar',
                'work_start_time': '09:00',
                'work_end_time': '17:00',
                'late_allowance_minutes': '15'
            }
            
            for key, value in default_settings.items():
                # Check if setting exists before saving
                current_settings = self.get_all_settings()
                if key not in current_settings:
                    self.save_setting(key, value)
            
            print("[DB Manager] Default data setup completed")
            
        except Exception as e:
            print(f"[DB Manager] Error setting up default data: {e}")
    
    def get_employee(self, employee_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على موظف"""
        return self.get_employee_by_id(employee_id)
    
    def record_attendance(self, attendance_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """تسجيل حضور"""
        try:
            result_id = self.add_attendance_record(attendance_data)
            if result_id:
                return {
                    'id': result_id,
                    'employee_id': attendance_data.get('employee_id'),
                    'employee_name': attendance_data.get('employee_name'),
                    'check_time': attendance_data.get('check_time'),
                    'date': attendance_data.get('date'),
                    'type': attendance_data.get('type', 'Check-In')
                }
            return None
        except Exception as e:
            print(f"[DB Manager] Error recording attendance: {e}")
            return None
    
    def delete_employee(self, employee_id: str) -> bool:
        """Delete موظف"""
        try:
            return self._execute_query_with_commit("DELETE FROM employees WHERE id = ?", (employee_id,))
        except Exception as e:
            print(f"[DB Manager] Error deleting employee: {e}")
            return False
    
    def get_attendance_by_id(self, attendance_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على سجل حضور"""
        try:
            conn = self._create_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM attendance WHERE id = ?", (attendance_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, result))
            return None
            
        except Exception as e:
            print(f"[DB Manager] Error getting attendance: {e}")
            return None
    
    def add_user(self, user_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Add مستخدم"""
        try:
            if isinstance(user_data, dict):
                username = user_data.get('username')
                password = user_data.get('password', 'default123')
                role = user_data.get('role', 'user')
            else:
                username = user_data
                password = 'default123'
                role = 'user'
            
            hashed_password = hashlib.sha256(password.encode()).hexdigest()
            user_id = self._execute_query_with_commit('INSERT INTO "users" (username, password, role) VALUES (?, ?, ?)', (username, hashed_password, role))
            
            if user_id:
                return {
                    'id': user_id,
                    'username': username,
                    'role': role
                }
            return None
            
        except Exception as e:
            print(f"[DB Manager] Error adding user: {e}")
            return None
    
    def update_setting(self, key: str, value: Any) -> bool:
        """Update إعداد"""
        try:
            self.save_setting(key, str(value))
            return True
        except Exception as e:
            print(f"[DB Manager] Error updating setting: {e}")
            return False

    def get_attendance_records_for_date(self, target_date: str) -> List[Dict[str, Any]]:
        query = "SELECT * FROM attendance WHERE date = ? ORDER BY check_time ASC"
        return self._execute_query(query, (target_date,), fetch=True)

    def get_last_attendance_type(self, employee_id: str, date_str: str) -> Optional[str]:
        query = "SELECT type FROM attendance WHERE employee_id = ? AND date = ? ORDER BY id DESC LIMIT 1"
        result = self._execute_query(query, (employee_id, date_str), fetch=True)
        if result and isinstance(result, list) and len(result) > 0:
            return result[0].get('type')
        elif result and isinstance(result, dict):
            return result.get('type')
        return None

    def get_check_in_today(self, employee_id, date_str):
        """
        يجلب أول وقت تسجيل دخول لموظف في يوم محدد.
        يعيد سلسلة نصية (HH:MM:SS) أو None.
        """
        result = self._execute_query("SELECT check_time FROM attendance WHERE employee_id = ? AND date = ? AND type = 'Check-In' ORDER BY id ASC LIMIT 1", (employee_id, date_str), fetch=True)
        if result and isinstance(result, list) and len(result) > 0:
            return result[0].get('check_time')
        elif result and isinstance(result, dict):
            return result.get('check_time')
        return None
    
    # 🆕 دالة صحة النظام
    def get_system_health(self) -> Dict[str, Any]:
        """الحصول على صحة النظام"""
        try:
            health_status = {
                'overall_status': 'Healthy',
                'database_connected': True,
                'total_tables': 0,
                'total_records': 0,
                'last_check': datetime.now().isoformat(),
                'errors': []
            }
            
            # فحص الاتصال بقاعدة البيانات
            try:
                conn = self._create_connection()
                cursor = conn.cursor()
                
                # الحصول على عدد الجداول
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                health_status['total_tables'] = len(tables)
                
                # الحصول على إجمالي السجلات
                total_records = 0
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    total_records += count
                
                health_status['total_records'] = total_records
                conn.close()
                
            except Exception as e:
                health_status['database_connected'] = False
                health_status['overall_status'] = 'Unhealthy'
                health_status['errors'].append(f"Database connection error: {str(e)}")
            
            return health_status
            
        except Exception as e:
            return {
                'overall_status': 'Error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }