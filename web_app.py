import os
import datetime
import requests
from flask import Flask, render_template, request, jsonify

# استيراد الوحدات اللازمة
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from app.database.database_manager import DatabaseManager
from app.database.database_setup import setup_database
from app.utils.notifier import NOTIFIER_HOST, NOTIFIER_PORT
from app.version import APP_VERSION


# --- ========================================================= ---
# ---              بداية الإضافة: دوال مساعدة                  ---
# --- ========================================================= ---

from math import radians, cos, sin, asin, sqrt

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    تحسب المسافة بالأمتار بين نقطتين باستخدام صيغة Haversine.
    """
    # تحويل الدرجات إلى راديان
    lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])

    # صيغة Haversine
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371 # نصف قطر الأرض بالكيلومترات
    return c * r * 1000 # التحويل إلى أمتار

# --- ========================================================= ---
# ---                       نهاية الإضافة                        ---
# --- ========================================================= ---



# --- الإعدادات ---
# تأكد من إنشاء قاعدة البيانات والجداول عند تشغيل الخادم لأول مرة
setup_database()

app = Flask(__name__, template_folder='templates')
app.config['JSON_AS_ASCII'] = False
db_manager = DatabaseManager()
DEBUG_MODE = os.getenv('FLASK_DEBUG', '0') == '1'
PUBLIC_BASE_URL = os.getenv('PUBLIC_BASE_URL')  # مثال: https://example.com
GITHUB_OWNER = os.getenv('GITHUB_OWNER')
GITHUB_REPO = os.getenv('GITHUB_REPO')
INSTALLER_NAME = os.getenv('INSTALLER_NAME', 'AttendanceAdminInstaller.exe')

def find_employee_by_identifier(identifier):
    """
    تبحث عن الموظف بذكاء باستخدام الكود الوظيفي أو رقم الهاتف.
    """
    if len(identifier) > 6 and identifier.isdigit():
        employee = db_manager.get_employee_by_phone(identifier)
        if employee: return employee
    return db_manager.get_employee_by_code(identifier)

# --- الطرق (Routes) ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/healthz')
def healthz():
    return jsonify({'status': 'ok'}), 200

@app.route('/api/app-version')
def app_version_api():
    platform_q = request.args.get('platform', 'windows')
    channel = request.args.get('channel', 'stable')
    notes = "- تحسينات عامة وإصلاحات أخطاء.\n- دعم التحقق التلقائي من التحديثات."
    # مسار المثبّت ضمن المشروع (تجريبي محليًا)
    local_installer_path = os.path.join('deploy', 'deploy', 'output', INSTALLER_NAME)
    if GITHUB_OWNER and GITHUB_REPO:
        download_url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/download/v{APP_VERSION}/{INSTALLER_NAME}"
    elif PUBLIC_BASE_URL:
        download_url = f"{PUBLIC_BASE_URL}/downloads/AttendanceAdminInstaller.exe"
    else:
        # للبيئة المحلية يمكن تقديمه مباشرة عبر static-like
        download_url = request.host_url.rstrip('/') + '/download/installer'
    return jsonify({
        'version': APP_VERSION,
        'notes': notes,
        'mandatory': False,
        'platform': platform_q,
        'channel': channel,
        'download_url': download_url
    })

@app.route('/download/installer')
def download_installer():
    path = os.path.join('deploy', 'deploy', 'output', INSTALLER_NAME)
    if not os.path.exists(path):
        return jsonify({'error': 'installer not found'}), 404
    def generate():
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(8192)
                if not chunk:
                    break
                yield chunk
    return app.response_class(generate(), mimetype='application/octet-stream', headers={
        'Content-Disposition': f'attachment; filename="{INSTALLER_NAME}"'
    })

@app.route('/api/employee-status', methods=['GET'])
def employee_status():
    """
    API مطور ليعيد ملفًا كاملاً عن الموظف للواجهة الجديدة.
    """
    identifier = request.args.get('identifier')
    if not identifier: return jsonify({'status': 'error', 'message': 'الإدخال مطلوب.'}), 400
    
    employee = find_employee_by_identifier(identifier)
    if not employee: return jsonify({'status': 'not_found'})
    
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    # --- حساب إحصائيات الشهر الحالي ---
    first_day_of_month = datetime.date.today().replace(day=1).strftime("%Y-%m-%d")
    monthly_attendance = db_manager.execute_query(
        "SELECT COUNT(DISTINCT date) as attendance_days FROM attendance WHERE employee_id = ? AND date BETWEEN ? AND ?",
        (employee['id'], first_day_of_month, today_str),
        fetchone=True
    )
    monthly_days_count = monthly_attendance['attendance_days'] if monthly_attendance else 0

    # --- باقي المنطق ---
    last_action = db_manager.get_last_action_today(employee['id'], today_str)
    all_todays_records = db_manager.get_attendance_by_date(today_str) or []
    employee_todays_records = [rec for rec in all_todays_records if rec['employee_id'] == employee['id']]
    next_action = 'Check-In' if last_action is None else 'Check-Out' if last_action == 'Check-In' else 'None'
    
    # --- بداية الكود الذي كان ناقصًا ---
    is_late = False
    if next_action == 'Check-In':
        settings = db_manager.get_all_settings()
        work_start_time_str = settings.get('work_start_time', '08:30:00')
        late_allowance_minutes = int(settings.get('late_allowance_minutes', '15'))
        work_start_time = datetime.datetime.strptime(work_start_time_str, "%H:%M:%S").time()
        deadline = (datetime.datetime.combine(datetime.date.min, work_start_time) + datetime.timedelta(minutes=late_allowance_minutes)).time()
        if datetime.datetime.now().time() > deadline:
            is_late = True
    # --- نهاية الكود الذي كان ناقصًا ---

    return jsonify({
        'status': 'found', 
        'next_action': next_action,
        'employee_name': employee.get('name'),
        'job_title': employee.get('job_title'),
        'is_late': is_late,
        'todays_log': employee_todays_records,
        'stats': {
            'monthly_attendance': monthly_days_count
        }
    })


@app.route('/api/check-in', methods=['POST'])
def check_in():
    """
    API لتسجيل الحضور، مع التحقق من الموقع الجغرافي كخطوة أولى.
    """
    data = request.json
    identifier, fingerprint, token, location, check_type, notes = (
        data.get('identifier'), data.get('fingerprint'), data.get('token'),
        data.get('location'), data.get('type'), data.get('notes')
    )

    if not all([identifier, fingerprint, token, location, check_type]):
        return jsonify({'status': 'error', 'message': 'بيانات الطلب غير مكتملة.'}), 400

    employee_to_check_in = find_employee_by_identifier(identifier)
    if not employee_to_check_in:
        return jsonify({'status': 'error', 'message': 'المعرّف غير مسجل بالنظام.'}), 404

    # --- منطق التحقق من الموقع الجغرافي (Geofencing) ---
    approved_locations = db_manager.get_all_locations()
    if not approved_locations:
        return jsonify({'status': 'error', 'message': 'لا توجد مواقع عمل معتمدة. يرجى مراجعة الإدارة.'}), 403

    employee_lat = location.get('lat')
    employee_lon = location.get('lon')
    if not employee_lat or not employee_lon:
        return jsonify({'status': 'error', 'message': 'فشل تحديد موقعك. يرجى السماح بذلك والمحاولة مرة أخرى.'}), 400

    closest_location, min_distance = None, float('inf')
    for loc in approved_locations:
        distance = calculate_distance(employee_lat, employee_lon, loc['latitude'], loc['longitude'])
        if distance < min_distance:
            min_distance = distance
            closest_location = loc

    if not closest_location or min_distance > closest_location['radius_meters']:
        loc_name = closest_location['name'] if closest_location else "any approved location"
        return jsonify({'status': 'error', 'message': f"أنت خارج نطاق العمل المعتمد. أقرب موقع ('{loc_name}') يبعد عنك مسافة {min_distance:.0f} متر."}), 403

    location_id_to_save = closest_location['id']
    location_name = closest_location['name']

    # --- بداية الكود الذي كان ناقصًا ---

    # --- منطق كشف الغش والأمان المتقدم ---
    owner_by_token = db_manager.get_employee_by_token(token)
    if owner_by_token and owner_by_token['id'] != employee_to_check_in['id']:
        return jsonify({'status': 'error', 'message': f"يا {owner_by_token['name']}, هذا المتصفح مرتبط بك."}), 403
    
    employee_token = employee_to_check_in.get('device_token')
    employee_fingerprint = employee_to_check_in.get('web_fingerprint')

    if employee_token:
        if employee_token == token:
            print(f"[AUTH] Success: Token matched for employee {employee_to_check_in['id']}.")
        elif employee_fingerprint == fingerprint:
            print(f"[AUTH] Token mismatch, but Canvas Fingerprint matched. Updating token...")
            db_manager.execute_query("UPDATE employees SET device_token = ? WHERE id = ?", (token, employee_to_check_in['id']), commit=True)
        else:
            print(f"[AUTH] FAILED: Token and Fingerprint mismatch for employee {employee_to_check_in['id']}.")
            return jsonify({'status': 'error', 'message': f"يا {employee_to_check_in['name']}, يجب عليك استخدام جهازك المسجل."}), 403
    else:
        print(f"[AUTH] First-time registration for employee {employee_to_check_in['id']}.")
        db_manager.update_employee_device_info(employee_to_check_in['id'], fingerprint, token)
        success_message = f"تم ربط هذا المتصفح بنجاح! مرحباً بك يا {employee_to_check_in['name']}."

    # --- منطق تسلسل الإجراءات ---
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    last_action = db_manager.get_last_action_today(employee_to_check_in['id'], today_str)
    if (check_type == 'Check-In' and last_action is not None):
        return jsonify({'status': 'error', 'message': 'لا يمكنك تسجيل الحضور مرتين.'}), 403
    if (check_type == 'Check-Out' and last_action != 'Check-In'):
        return jsonify({'status': 'error', 'message': 'لا يمكنك تسجيل الانصراف قبل الحضور.'}), 403

    # --- إعداد رسالة النجاح وحفظ البيانات ---
    if 'success_message' not in locals():
        success_message = f"تم تسجيل '{check_type}' بنجاح من موقع '{location_name}'."
    
    duration_hours = None
    if check_type == 'Check-Out':
        check_in_time_str = db_manager.get_check_in_time_today(employee_to_check_in['id'], today_str)
        if check_in_time_str:
            check_in_time = datetime.datetime.strptime(check_in_time_str, "%H:%M:%S").time()
            check_out_time = datetime.datetime.now().time()
            duration = datetime.datetime.combine(datetime.date.today(), check_out_time) - datetime.datetime.combine(datetime.date.today(), check_in_time)
            duration_hours = round(duration.total_seconds() / 3600, 2)
            
    now = datetime.datetime.now()
    attendance_data = {
        'employee_id': employee_to_check_in['id'], 'check_time': now.strftime("%H:%M:%S"),
        'date': now.strftime("%Y-%m-%d"), 'type': check_type,
        'location_id': location_id_to_save, 'notes': notes
    }
    record_id = db_manager.add_attendance_record(attendance_data)
    
    if record_id and duration_hours is not None:
        db_manager.update_checkout_with_duration(record_id, duration_hours)

    if record_id:
        try:
            notifier_url = f"http://{NOTIFIER_HOST}:{NOTIFIER_PORT}/notify"
            requests.get(notifier_url, timeout=0.5)
        except requests.exceptions.RequestException: pass
        return jsonify({'status': 'success', 'message': success_message})
    else:
        return jsonify({'status': 'error', 'message': 'حدث خطأ في الخادم أثناء حفظ السجل.'}), 500
    
    # --- نهاية الكود الذي كان ناقصًا ---

    
# --- بدء تشغيل الخادم ---
if __name__ == '__main__':
    print("--- Starting Web App Server (Local SQLite Mode) ---")
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5000')), debug=DEBUG_MODE)