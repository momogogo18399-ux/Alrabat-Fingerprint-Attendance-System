import sqlite3
import os
from app.utils.encryption import hash_password

DATABASE_FILE = "attendance.db"

def setup_database():
    if not os.path.exists(DATABASE_FILE):
        print("Database not found. Creating a new one...")
        try:
            conn = sqlite3.connect(DATABASE_FILE)
            create_tables(conn)
            create_default_settings(conn)
            create_default_admin(conn)
        except sqlite3.Error as e:
            print(f"Database error during setup: {e}")
        finally:
            if conn:
                conn.close()
                print("Database setup complete.")

def create_tables(conn: sqlite3.Connection):
    cursor = conn.cursor()
    
    # 1. جدول الموظفين بالبنية النهائية
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        employee_code TEXT NOT NULL UNIQUE,
        name TEXT NOT NULL, 
        job_title TEXT,
        department TEXT, 
        phone_number TEXT UNIQUE, 
        web_fingerprint TEXT,        -- بصمة المتصفح (للتدقيق الثانوي)
        device_token TEXT UNIQUE,    -- التوكن الدائم (للأمان الأساسي)
        zk_template TEXT,            -- قالب بصمة جهاز ZK
        status TEXT DEFAULT 'Active'
    );""")

    # ... باقي الجداول كما هي ...
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        username TEXT NOT NULL UNIQUE, 
        password TEXT NOT NULL, 
        role TEXT NOT NULL CHECK(role IN ('Viewer', 'Manager', 'HR', 'Admin'))
    );""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        employee_id INTEGER NOT NULL, 
        check_time TEXT NOT NULL,
        date TEXT NOT NULL, 
        type TEXT NOT NULL, 
        location_lat REAL, 
        location_lon REAL, 
        work_duration_hours REAL,
        notes TEXT,
        FOREIGN KEY (employee_id) REFERENCES employees (id) ON DELETE CASCADE
    );""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT DEFAULT CURRENT_TIMESTAMP, user_id INTEGER, action TEXT NOT NULL, FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL);""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT);""")
    
    print("All tables created successfully.")

def create_default_settings(conn: sqlite3.Connection):
    # ... (نفس الكود بدون تغيير) ...
    try:
        cursor = conn.cursor(); settings = {'work_start_time': '08:30:00','late_allowance_minutes': '15','theme': 'light','language': 'en'}
        for key, value in settings.items(): cursor.execute("INSERT OR IGNORE INTO app_settings (key, value) VALUES (?, ?)", (key, value))
        conn.commit(); print("Default settings inserted.")
    except sqlite3.Error as e: print(f"Error creating default settings: {e}")

def create_default_admin(conn: sqlite3.Connection):
    # ... (نفس الكود بدون تغيير) ...
    try:
        cursor = conn.cursor(); cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        if cursor.fetchone() is None:
            hashed_pass = hash_password('admin')
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", ('admin', hashed_pass, 'Admin'))
            conn.commit(); print("Default admin user created.")
    except sqlite3.Error as e: print(f"Error creating default admin: {e}")