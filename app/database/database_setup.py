import os
import sqlite3
from typing import Optional

# هذا الاستيراد مهم لإنشاء المستخدم المدير الافتراضي
from app.utils.encryption import hash_password

DATABASE_FILE = "attendance.db"
DATABASE_URL = os.getenv("DATABASE_URL")
IS_POSTGRES = bool(DATABASE_URL and DATABASE_URL.startswith("postgres"))

try:
    import psycopg2
except Exception:
    psycopg2 = None

def setup_database():
    """تهيئة قاعدة البيانات. تستخدم PostgreSQL إذا تم ضبط DATABASE_URL، وإلا SQLite."""
    if IS_POSTGRES:
        if psycopg2 is None:
            print("psycopg2 not installed; cannot set up PostgreSQL schema.")
            return
        try:
            with psycopg2.connect(DATABASE_URL) as conn:
                with conn.cursor() as cur:
                    create_tables_postgres(cur)
                    create_default_settings_postgres(cur)
                    create_default_admin_postgres(cur)
                conn.commit()
            print("PostgreSQL schema ensured.")
        except Exception as e:
            print(f"PostgreSQL setup error: {e}")
        return

    # SQLite path
    conn = None
    try:
        is_new = not os.path.exists(DATABASE_FILE)
        if is_new:
            print("Database not found. Creating a new one for local use...")
        conn = sqlite3.connect(DATABASE_FILE)
        if is_new:
            create_tables(conn)
            create_default_settings(conn)
            create_default_admin(conn)
            print("Local database setup complete.")
        # Always run lightweight migrations to keep schema up-to-date
        try:
            migrate_sqlite_schema(conn)
        except Exception as e:
            print(f"SQLite migration warning: {e}")
    except sqlite3.Error as e:
        print(f"Database error during setup: {e}")
    finally:
        if conn:
            conn.close()

def create_tables(conn: sqlite3.Connection):
    """
    تنشئ جميع الجداول اللازمة للتطبيق بالبنية النهائية والصحيحة لـ SQLite.
    """
    cursor = conn.cursor()
    
    # 1. جدول الموظفين (مع كل الحقول المطلوبة)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        employee_code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL, 
        job_title TEXT,
        department TEXT, 
        phone_number TEXT UNIQUE, 
        web_fingerprint TEXT,
        device_token TEXT UNIQUE,
        zk_template TEXT,
        qr_code TEXT UNIQUE,
        status TEXT DEFAULT 'Active'
    );""")

    # 2. جدول مستخدمي البرنامج
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT NOT NULL UNIQUE, 
        password TEXT NOT NULL, 
        role TEXT NOT NULL CHECK(role IN ('Viewer', 'Manager', 'HR', 'Admin', 'Scanner'))
    );""")

    # 3. جدول الحضور (مُعدّل)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        employee_id INTEGER NOT NULL, 
        check_time TEXT NOT NULL,
        date TEXT NOT NULL, 
        type TEXT NOT NULL, 
        location_id INTEGER, --  <-- الحقل الجديد لربط الموقع
        notes TEXT,
        work_duration_hours REAL,
        FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE,
        FOREIGN KEY (location_id) REFERENCES locations (id) ON DELETE SET NULL -- <-- علاقة جديدة
    );""")

    # 4. جدول سجلات النشاط
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
        user_id INTEGER, 
        action TEXT NOT NULL, 
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
    );""")

    # 5. جدول إعدادات التطبيق
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );""")
    


        # 6. جدول المواقع المعتمدة (جدول جديد بالكامل)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS locations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        latitude REAL NOT NULL,
        longitude REAL NOT NULL,
        radius_meters INTEGER NOT NULL
    );""")



    # 7. جدول الإعدادات الخاصة بالمواقع (جدول جديد بالكامل)
    conn.commit()
    print("All tables created successfully.")

    # مهاجرة قيد الدور إذا كان الجدول قديماً لا يحتوي على Scanner
    try:
        cur2 = conn.cursor()
        cur2.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
        row = cur2.fetchone()
        create_sql = row[0] if row else ''
        if "Scanner" not in create_sql:
            # إعادة إنشاء الجدول لتحديث CHECK constraint
            cur2.execute("PRAGMA foreign_keys=off")
            cur2.execute("BEGIN TRANSACTION")
            cur2.execute("CREATE TABLE users_new (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('Viewer','Manager','HR','Admin','Scanner')))")
            cur2.execute("INSERT INTO users_new (id, username, password, role) SELECT id, username, password, role FROM users")
            cur2.execute("DROP TABLE users")
            cur2.execute("ALTER TABLE users_new RENAME TO users")
            cur2.execute("COMMIT")
            cur2.execute("PRAGMA foreign_keys=on")
            print("[Migration] Updated users.role CHECK to include 'Scanner'.")
    except Exception as e:
        print(f"[Migration] users.role check update failed: {e}")



        # 8. جدول الإجازات الرسمية (جدول جديد بالكامل)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS holidays (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL UNIQUE,
        description TEXT NOT NULL
    );""")

    # 9. جدول جلسات دخول المشرفين (جديد)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS admin_sessions (
        token TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    );""")

    # 10. إنشاء فهارس لتحسين الأداء على الاستعلامات الشائعة
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_emp_date ON attendance(employee_id, date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_attendance_type ON attendance(type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_employees_code ON employees(employee_code)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_employees_phone ON employees(phone_number)")
    conn.commit()




def migrate_sqlite_schema(conn: sqlite3.Connection):
    """ترقيات بسيطة للحفاظ على المخطط مواكباً (تشمل إضافة دور Scanner)."""
    try:
        cur = conn.cursor()
        # تحقق من دعم دور Scanner في users
        cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users'")
        row = cur.fetchone()
        create_sql = row[0] if row else ''
        if 'CHECK(role IN (\'Viewer\'' not in create_sql:
            # إذا كان الجدول مختلفاً جداً، نتخطى (حالات نادرة)
            pass
        if "Scanner" not in create_sql:
            cur.execute("PRAGMA foreign_keys=off")
            cur.execute("BEGIN TRANSACTION")
            cur.execute("CREATE TABLE users_new (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL UNIQUE, password TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('Viewer','Manager','HR','Admin','Scanner')))")
            cur.execute("INSERT INTO users_new (id, username, password, role) SELECT id, username, password, role FROM users")
            cur.execute("DROP TABLE users")
            cur.execute("ALTER TABLE users_new RENAME TO users")
            cur.execute("COMMIT")
            cur.execute("PRAGMA foreign_keys=on")
            print("[Migration] users table updated to include Scanner role.")
    except Exception as e:
        print(f"[Migration] Failed to update users table: {e}")

def create_default_settings(conn: sqlite3.Connection):
    """
    تضيف الإعدادات الافتراضية للتطبيق عند أول تشغيل.
    """
    try:
        cursor = conn.cursor()
        settings = {
            'work_start_time': '08:30:00',
            'late_allowance_minutes': '15',
            'theme': 'light',
            'language': 'en'
        }
        for key, value in settings.items():
            cursor.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit()
        print("Default settings inserted.")
    except sqlite3.Error as e:
        print(f"Error creating default settings: {e}")

def create_default_admin(conn: sqlite3.Connection):
    """
    تنشئ حساب المدير الافتراضي (admin/admin).
    """
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if cursor.fetchone() is None:
            hashed_pass = hash_password('admin')
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                           ('admin', hashed_pass, 'Admin'))
            conn.commit()
            print("Default admin user (admin/admin) created.")
    except sqlite3.Error as e:
        print(f"Error creating default admin: {e}")


# ================= PostgreSQL schema helpers =================
def create_tables_postgres(cur):
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS employees (
            id SERIAL PRIMARY KEY,
            employee_code TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            job_title TEXT,
            department TEXT,
            phone_number TEXT UNIQUE,
            web_fingerprint TEXT,
            device_token TEXT UNIQUE,
            zk_template TEXT,
            qr_code TEXT UNIQUE,
            status TEXT DEFAULT 'Active'
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('Viewer', 'Manager', 'HR', 'Admin', 'Scanner'))
        );
        """
    )

    # ترقية قيد الدور في بوستجرس إذا كان قديماً
    try:
        cur.execute("ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check")
        cur.execute("ALTER TABLE users ADD CONSTRAINT users_role_check CHECK (role IN ('Viewer','Manager','HR','Admin','Scanner'))")
    except Exception:
        pass

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS locations (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL UNIQUE,
            latitude DOUBLE PRECISION NOT NULL,
            longitude DOUBLE PRECISION NOT NULL,
            radius_meters INTEGER NOT NULL
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS attendance (
            id SERIAL PRIMARY KEY,
            employee_id INTEGER NOT NULL REFERENCES employees(id) ON DELETE CASCADE,
            check_time TEXT NOT NULL,
            date TEXT NOT NULL,
            type TEXT NOT NULL,
            location_id INTEGER REFERENCES locations(id) ON DELETE SET NULL,
            notes TEXT,
            work_duration_hours DOUBLE PRECISION
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS logs (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            action TEXT NOT NULL
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT
        );
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # indices
    cur.execute("CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_attendance_emp_date ON attendance(employee_id, date)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_attendance_type ON attendance(type)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_employees_code ON employees(employee_code)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_employees_phone ON employees(phone_number)")


def create_default_settings_postgres(cur):
    settings = {
        'work_start_time': '08:30:00',
        'late_allowance_minutes': '15',
        'theme': 'light',
        'language': 'en'
    }
    for key, value in settings.items():
        cur.execute(
            "INSERT INTO app_settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
            (key, value)
        )


def create_default_admin_postgres(cur):
    cur.execute("SELECT id FROM users WHERE username = 'admin'")
    exists = cur.fetchone()
    if not exists:
        from app.utils.encryption import hash_password
        hashed_pass = hash_password('admin')
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
            ('admin', hashed_pass, 'Admin')
        )