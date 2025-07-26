import sqlite3
import datetime

DATABASE_FILE = "attendance.db"

def log_activity(user_id: int, action: str):
    """
    يسجل نشاطًا قام به المستخدم في قاعدة البيانات.
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            "INSERT INTO logs (timestamp, user_id, action) VALUES (?, ?, ?)",
            (timestamp, user_id, action)
        )
        conn.commit()
    except sqlite3.Error as e:
        print(f"Error logging activity: {e}")
    finally:
        if conn:
            conn.close()