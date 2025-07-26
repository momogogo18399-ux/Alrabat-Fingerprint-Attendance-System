import os
import datetime
import requests
from flask import Flask, render_template, request, jsonify

# استيراد مدير قاعدة البيانات والمنبه
from app.database.database_manager import DatabaseManager
from app.utils.notifier import NOTIFIER_HOST, NOTIFIER_PORT

# --- ========================================================= ---
# ---       إعداد مرن لقاعدة البيانات (للإنتاج والتطوير)        ---
# --- ========================================================= ---

# 1. اقرأ عنوان URL من متغيرات البيئة. Railway/Supabase سيوفر هذا المتغير تلقائيًا.
DATABASE_URL = os.environ.get("DATABASE_URL")

# 2. قم بإنشاء مدير قاعدة البيانات بناءً على البيئة
db_manager = None
if DATABASE_URL:
    # بيئة الإنتاج: اتصل بـ PostgreSQL
    print("[INFO] Production environment detected. Connecting to PostgreSQL database.")
    db_manager = DatabaseManager(db_url=DATABASE_URL)
else:
    # بيئة التطوير المحلي: استخدم SQLite
    print("[INFO] Development environment detected. Using local SQLite database (attendance.db).")
    db_manager = DatabaseManager() 

# --- ========================================================= ---


app = Flask(__name__)


def find_employee_by_identifier(identifier):
    """
    تبحث عن الموظف بذكاء باستخدام الكود الوظيفي أو رقم الهاتف.
    """
    if not db_manager: return None
    
    # نفترض أن أرقام الهواتف أطول من الأكواد الوظيفية وتحتوي على أرقام فقط
    if len(identifier) > 6 and identifier.isdigit():
        employee = db_manager.get_employee_by_phone(identifier)
        if employee:
            return employee
    
    # إذا لم يتم العثور عليه بالهاتف أو إذا كان الإدخال قصيرًا، نبحث بالكود
    return db_manager.get_employee_by_code(identifier)

# --- الطرق (Routes) ---

@app.route('/')
def index():
    """يعرض صفحة تسجيل الحضور الرئيسية."""
    return render_template('index.html')

@app.route('/api/employee-status', methods=['GET'])
def employee_status():
    """API مطور لتحديد حالة الموظف، مع إرجاع بيانات كاملة للواجهة."""
    if not db_manager: return jsonify({'status': 'error', 'message': 'Database not configured.'}), 503

    identifier = request.args.get('identifier')
    if not identifier:
        return jsonify({'status': 'error', 'message': 'الإدخال مطلوب.'}), 400
    
    employee = find_employee_by_identifier(identifier)
    if not employee:
        return jsonify({'status': 'not_found'})
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    last_action = db_manager.get_last_action_today(employee['id'], today_str)
    
    all_todays_records = db_manager.get_attendance_by_date(today_str) or []
    employee_todays_records = [rec for rec in all_todays_records if rec['employee_id'] == employee['id']]
    
    next_action = 'Check-In' if last_action is None else 'Check-Out' if last_action == 'Check-In' else 'None'
    
    is_late = False
    if next_action == 'Check-In':
        settings = db_manager.get_all_settings()
        work_start_time_str = settings.get('work_start_time', '08:30:00')
        late_allowance_minutes = int(settings.get('late_allowance_minutes', '15'))
        work_start_time = datetime.datetime.strptime(work_start_time_str, "%H:%M:%S").time()
        deadline = (datetime.datetime.combine(datetime.date.min, work_start_time) + datetime.timedelta(minutes=late_allowance_minutes)).time()
        if datetime.datetime.now().time() > deadline:
            is_late = True

    return jsonify({
        'status': 'found', 
        'next_action': next_action,
        'employee_name': employee.get('name'),
        'is_late': is_late,
        'todays_log': employee_todays_records
    })

@app.route('/api/check-in', methods=['POST'])
def check_in():
    """API لتسجيل حدث الحضور أو الانصراف، مع سلسلة كاملة من عمليات التحقق."""
    if not db_manager: return jsonify({'status': 'error', 'message': 'Database not configured.'}), 503
        
    data = request.json
    identifier, fingerprint, token, location, check_type, notes = (
        data.get('identifier'), data.get('fingerprint'), data.get('token'),
        data.get('location'), data.get('type'), data.get('notes')
    )

    if not all([identifier, fingerprint, token, location, check_type]):
        return jsonify({'status': 'error', 'message': 'بيانات الطلب غير مكتملة.'}), 400

    employee_to_check_in = find_employee_by_identifier(identifier)
    if not employee_to_check_in:
        return jsonify({'status': 'error', 'message': 'رقم الهاتف أو الكود الوظيفي غير موجود بالنظام.'}), 404

    # --- منطق كشف الغش والأمان المتقدم ---
    owner_by_token = db_manager.get_employee_by_token(token)
    if owner_by_token and owner_by_token['id'] != employee_to_check_in['id']:
        return jsonify({'status': 'error', 'message': f"يا {owner_by_token['name']}، لا يمكنك استخدام هذا المتصفح لتسجيل حضور شخص آخر. هذا المتصفح مرتبط بك."}), 403

    employee_token = employee_to_check_in.get('device_token')
    employee_fingerprint = employee_to_check_in.get('web_fingerprint')

    if employee_token:
        if employee_token != token:
            return jsonify({'status': 'error', 'message': f"يا {employee_to_check_in['name']}، يجب عليك استخدام نفس المتصفح الذي سجلت به أول مرة."}), 403
        if employee_fingerprint != fingerprint:
            return jsonify({'status': 'error', 'message': 'تم اكتشاف تغيير في خصائص المتصفح. يرجى مراجعة الإدارة.'}), 403
    else:
        db_manager.update_employee_device_info(employee_to_check_in['id'], fingerprint, token)
        success_message = f"تم ربط هذا المتصفح بنجاح! مرحباً بك يا {employee_to_check_in['name']}."

    # --- منطق تسلسل الإجراءات ---
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    last_action = db_manager.get_last_action_today(employee_to_check_in['id'], today_str)
    if (check_type == 'Check-In' and last_action is not None):
        return jsonify({'status': 'error', 'message': 'لا يمكنك تسجيل الحضور مرتين. يجب تسجيل الانصراف أولاً.'}), 403
    if (check_type == 'Check-Out' and last_action != 'Check-In'):
        return jsonify({'status': 'error', 'message': 'لا يمكنك تسجيل الانصراف قبل تسجيل الحضور.'}), 403

    if 'success_message' not in locals():
        success_message = f"تم تسجيل '{check_type}' بنجاح يا {employee_to_check_in['name']}."

    # --- حفظ البيانات وحساب المدة ---
    duration_hours = None
    if check_type == 'Check-Out':
        check_in_time_str_obj = db_manager.get_check_in_time_today(employee_to_check_in['id'], today_str)
        if check_in_time_str_obj:
            check_in_time_str = check_in_time_str_obj.get('check_time')
            check_in_time = datetime.datetime.strptime(check_in_time_str, "%H:%M:%S").time()
            check_out_time = datetime.datetime.now().time()
            duration = datetime.datetime.combine(datetime.date.today(), check_out_time) - datetime.datetime.combine(datetime.date.today(), check_in_time)
            duration_hours = round(duration.total_seconds() / 3600, 2)
            
    now = datetime.datetime.now()
    attendance_data = {'employee_id': employee_to_check_in['id'], 'check_time': now.strftime("%H:%M:%S"), 'date': now.strftime("%Y-%m-%d"), 'type': check_type, 'lat': location.get('lat'), 'lon': location.get('lon'), 'notes': notes}
    record_id = db_manager.add_attendance_record(attendance_data)
    
    if record_id and duration_hours is not None:
        db_manager.update_checkout_with_duration(record_id, duration_hours)

    if record_id:
        try:
            notifier_url = f"http://{NOTIFIER_HOST}:{NOTIFIER_PORT}/notify"
            requests.get(notifier_url, timeout=0.5)
            print(f"[Web App] Sent update signal to {notifier_url}")
        except requests.exceptions.RequestException:
            pass
        return jsonify({'status': 'success', 'message': success_message})
    else:
        return jsonify({'status': 'error', 'message': 'حدث خطأ في الخادم أثناء حفظ السجل.'}), 500

# --- بدء تشغيل الخادم ---
if __name__ == '__main__':
    if not db_manager:
        print("[FATAL ERROR] Could not start server. Database is not configured.")
    else:
        print("--- Starting Flask Server in Development Mode ---")
        app.run(host='0.0.0.0', port=5000, debug=True)