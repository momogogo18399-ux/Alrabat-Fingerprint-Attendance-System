import os
import datetime
import requests
from flask import Flask, render_template, request, jsonify
import uuid

# استيراد الوحدات اللازمة
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from app.database.database_manager import DatabaseManager
from app.database.database_setup import setup_database

from app.version import APP_VERSION


# --- ========================================================= ---
# ---              بداية الإضافة: دوال مساعدة                  ---
# --- ========================================================= ---

# --- بداية الإضافة: نظام الترجمة للرسائل ---
MESSAGES = {
    'en': {
        'input_required': 'Input is required.',
        'incomplete_data': 'Request data is incomplete.',
        'login_missing_creds': 'Please enter username and password.',
        'login_user_not_found': 'User not found.',
        'login_invalid_creds': 'Invalid credentials.',
        'login_no_permission': 'You do not have permission to use admin mode.',
        'login_failed': 'Login failed: {error}',
        'employee_not_found': 'Identifier is not registered in the system.',
        'no_approved_locations': 'No approved work locations found. Please contact administration.',
        'location_fail': 'Failed to determine your location. Please grant permission and try again.',
        'out_of_range': "You are outside the approved work range. The nearest location ('{loc_name}') is {distance:.0f} meters away.",
        'browser_linked_to_other': "Hey {name}, this browser is already linked to you.",
        'use_registered_device': "Hey {name}, you must use your registered device.",
        'browser_linked_success': "This browser has been successfully linked! Welcome, {name}.",
        'checkin_twice': 'You cannot check-in twice.',
        'checkout_before_checkin': 'You cannot check-out before checking in.',
        'record_success': "'{check_type}' has been successfully recorded from '{location_name}'.",
        'server_error': 'A server error occurred while saving the record.',
        'unauthorized': 'Unauthorized access. Please log in.'
    },
    'ar': {
        'input_required': 'الإدخال مطلوب.',
        'incomplete_data': 'بيانات الطلب غير مكتملة.',
        'login_missing_creds': 'يرجى إدخال اسم المستخدم وكلمة المرور.',
        'login_user_not_found': 'مستخدم غير موجود.',
        'login_invalid_creds': 'بيانات اعتماد غير صحيحة.',
        'login_no_permission': 'ليست لديك صلاحية استخدام وضع المسؤول.',
        'login_failed': 'فشل تسجيل الدخول: {error}',
        'employee_not_found': 'المعرّف غير مسجل بالنظام.',
        'no_approved_locations': 'لا توجد مواقع عمل معتمدة. يرجى مراجعة الإدارة.',
        'location_fail': 'فشل تحديد موقعك. يرجى السماح بذلك والمحاولة مرة أخرى.',
        'out_of_range': "أنت خارج نطاق العمل المعتمد. أقرب موقع ('{loc_name}') يبعد عنك مسافة {distance:.0f} متر.",
        'browser_linked_to_other': "يا {name}, هذا المتصفح مرتبط بك.",
        'use_registered_device': "يا {name}, يجب عليك استخدام جهازك المسجل.",
        'browser_linked_success': "تم ربط هذا المتصفح بنجاح! مرحباً بك يا {name}.",
        'checkin_twice': 'لا يمكنك تسجيل الحضور مرتين.',
        'checkout_before_checkin': 'لا يمكنك تسجيل الانصراف قبل الحضور.',
        'record_success': "تم تسجيل '{check_type}' بنجاح من موقع '{location_name}'.",
        'server_error': 'حدث خطأ في الخادم أثناء حفظ السجل.',
        'unauthorized': 'وصول غير مصرح به. يرجى تسجيل الدخول.'
    }
}

def get_message(key, lang='ar', **kwargs):
    """Gets a translated message."""
    # Fallback to 'ar' if lang is not supported
    lang = lang if lang in MESSAGES else 'ar'
    message_template = MESSAGES.get(lang, MESSAGES['ar']).get(key, "An unknown error occurred.")
    return message_template.format(**kwargs)
# --- نهاية الإضافة ---

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
@app.route('/api/login', methods=['POST'])
def login_api():
    """تسجيل دخول بسيط للمستخدمين الموجودين في جدول users وإرجاع رمز جلسة."""
    try:
        lang = request.headers.get('Accept-Language', 'ar').split(',')[0].split('-')[0]
        payload = request.get_json(force=True)
        username = (payload.get('username') or '').strip()
        password = payload.get('password') or ''
        if not username or not password:
            return jsonify({'success': False, 'message': get_message('login_missing_creds', lang)}), 400

        from app.utils.encryption import check_password
        user = db_manager.get_user_by_username(username)
        if not user:
            return jsonify({'success': False, 'message': get_message('login_user_not_found', lang)}), 404
        if not check_password(password, user['password']):
            return jsonify({'success': False, 'message': get_message('login_invalid_creds', lang)}), 401

        # السماح فقط لأدوار معينة باستخدام وضع المسؤول لمسح QR
        allowed_roles = {'Admin', 'Manager', 'HR', 'Scanner'}
        if user['role'] not in allowed_roles:
            return jsonify({'success': False, 'message': get_message('login_no_permission', lang)}), 403

        token = str(uuid.uuid4())
        db_manager.create_admin_session(user['id'], token)
        
        return jsonify({'success': True, 'token': token, 'role': user['role'], 'username': user['username']})
    except Exception as e:
        return jsonify({'success': False, 'message': get_message('login_failed', lang, error=str(e))}), 500


@app.route('/healthz')
def healthz():
    return jsonify({'status': 'ok'}), 200

@app.route('/api/app-version')
def app_version_api():
    platform_q = request.args.get('platform', 'windows')
    channel = request.args.get('channel', 'stable')
    
    # ملاحظات التحديث - يمكن تحديثها من متغير البيئة
    notes = os.getenv('UPDATE_NOTES', "- تحسينات عامة وإصلاحات أخطاء.\n- دعم التحقق التلقائي من التحديثات.\n- تحسينات في الأداء والاستقرار.")
    
    # تحديد URL التحميل
    download_url = None
    
    # أولوية: GitHub Releases
    if GITHUB_OWNER and GITHUB_REPO:
        download_url = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}/releases/download/v{APP_VERSION}/{INSTALLER_NAME}"
    
    # ثانوية: PUBLIC_BASE_URL
    elif PUBLIC_BASE_URL:
        download_url = f"{PUBLIC_BASE_URL}/downloads/{INSTALLER_NAME}"
    
    # ثالثية: الخادم المحلي (للاختبار)
    else:
        download_url = request.host_url.rstrip('/') + '/download/installer'
    
    # التحقق من إجبارية التحديث
    mandatory_update = os.getenv('MANDATORY_UPDATE', 'false').lower() == 'true'
    
    # إضافة معلومات إضافية للتحديث
    response_data = {
        'version': APP_VERSION,
        'notes': notes,
        'mandatory': mandatory_update,
        'platform': platform_q,
        'channel': channel,
        'download_url': download_url,
        'release_date': datetime.datetime.now().isoformat(),
        'min_version': os.getenv('MIN_SUPPORTED_VERSION', '1.0.0'),
        'checksum': None  # يمكن إضافة checksum للملف لاحقاً
    }
    
    # إضافة headers للأمان
    response = jsonify(response_data)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    
    return response

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
    lang = request.headers.get('Accept-Language', 'ar').split(',')[0].split('-')[0]
    identifier = request.args.get('identifier')
    if not identifier: return jsonify({'status': 'error', 'message': get_message('input_required', lang)}), 400
    
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
    lang = request.headers.get('Accept-Language', 'ar').split(',')[0].split('-')[0]
    data = request.json
    identifier, fingerprint, token, location, check_type, notes = (
        data.get('identifier'), data.get('fingerprint'), data.get('token'),
        data.get('location'), data.get('type'), data.get('notes')
    )

    if not all([identifier, fingerprint, token, location, check_type]):
        return jsonify({'status': 'error', 'message': get_message('incomplete_data', lang)}), 400

    employee_to_check_in = find_employee_by_identifier(identifier)
    if not employee_to_check_in:
        return jsonify({'status': 'error', 'message': get_message('employee_not_found', lang)}), 404

    # --- منطق التحقق من الموقع الجغرافي (Geofencing) ---
    approved_locations = db_manager.get_all_locations()
    if not approved_locations:
        return jsonify({'status': 'error', 'message': get_message('no_approved_locations', lang)}), 403

    employee_lat = location.get('lat')
    employee_lon = location.get('lon')
    if not employee_lat or not employee_lon:
        return jsonify({'status': 'error', 'message': get_message('location_fail', lang)}), 400

    closest_location, min_distance = None, float('inf')
    for loc in approved_locations:
        distance = calculate_distance(employee_lat, employee_lon, loc['latitude'], loc['longitude'])
        if distance < min_distance:
            min_distance = distance
            closest_location = loc

    if not closest_location or min_distance > closest_location['radius_meters']:
        loc_name = closest_location['name'] if closest_location else "any approved location"
        return jsonify({'status': 'error', 'message': get_message('out_of_range', lang, loc_name=loc_name, distance=min_distance)}), 403

    location_id_to_save = closest_location['id']
    location_name = closest_location['name']

    # --- بداية الكود الذي كان ناقصًا ---

    # --- منطق كشف الغش والأمان المتقدم ---
    owner_by_token = db_manager.get_employee_by_token(token)
    if owner_by_token and owner_by_token['id'] != employee_to_check_in['id']:
        return jsonify({'status': 'error', 'message': get_message('browser_linked_to_other', lang, name=owner_by_token['name'])}), 403
    
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
            return jsonify({'status': 'error', 'message': get_message('use_registered_device', lang, name=employee_to_check_in['name'])}), 403
    else:
        print(f"[AUTH] First-time registration for employee {employee_to_check_in['id']}.")
        db_manager.update_employee_device_info(employee_to_check_in['id'], fingerprint, token)
        success_message = get_message('browser_linked_success', lang, name=employee_to_check_in['name'])

    # --- منطق تسلسل الإجراءات ---
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    last_action = db_manager.get_last_action_today(employee_to_check_in['id'], today_str)
    if (check_type == 'Check-In' and last_action is not None):
        return jsonify({'status': 'error', 'message': get_message('checkin_twice', lang)}), 403
    if (check_type == 'Check-Out' and last_action != 'Check-In'):
        return jsonify({'status': 'error', 'message': get_message('checkout_before_checkin', lang)}), 403

    # --- إعداد رسالة النجاح وحفظ البيانات ---
    if 'success_message' not in locals():
        success_message = get_message('record_success', lang, check_type=check_type, location_name=location_name)
    
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
        
        return jsonify({'status': 'success', 'message': success_message})
    else:
        return jsonify({'status': 'error', 'message': get_message('server_error', lang)}), 500
    
    # --- نهاية الكود الذي كان ناقصًا ---

@app.route('/qr-scanner')
def qr_scanner():
    """صفحة مسح رموز QR للموظفين"""
    return render_template('qr_scanner.html')

@app.route('/api/scan-qr', methods=['POST'])
def scan_qr_api():
    """API لمعالجة رموز QR المسحوبة"""
    try:
        lang = request.headers.get('Accept-Language', 'ar').split(',')[0].split('-')[0]
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': get_message('unauthorized', lang)}), 401
        
        token = auth_header.split(' ')[1]
        admin_user = db_manager.validate_admin_session(token)
        if not admin_user:
            return jsonify({'success': False, 'error': get_message('unauthorized', lang)}), 401

        data = request.get_json()
        qr_code = data.get('qr_code', '').strip()
        
        if not qr_code:
            return jsonify({'success': False, 'error': 'رمز QR فارغ'}), 400
        
        # التحقق من صحة الرمز
        from app.utils.qr_manager import QRCodeManager
        qr_manager = QRCodeManager()
        
        result = qr_manager.verify_qr_code(qr_code)
        if not result or not result.get('is_valid'):
            return jsonify({'success': False, 'error': 'رمز QR غير صالح أو منتهي الصلاحية'}), 400
        
        # البحث عن الموظف
        employee_id = result.get('employee_id')
        employee = db_manager.get_employee_by_id(employee_id)
        
        if not employee:
            return jsonify({'success': False, 'error': 'لم يتم العثور على الموظف'}), 404
        
        # تسجيل الحضور
        current_time = datetime.datetime.now()
        current_date = current_time.strftime('%Y-%m-%d')
        current_time_str = current_time.strftime('%H:%M:%S')
        
        # التحقق من وجود تسجيل حضور اليوم
        existing_attendance = db_manager.get_attendance_by_employee_date(employee_id, current_date)
        
        if existing_attendance:
            # إذا كان هناك تسجيل حضور، سجل انصراف
            attendance_type = 'check_out'
            message = f"تم تسجيل انصراف: {employee['name']} في {current_time_str}"
        else:
            # إذا لم يكن هناك تسجيل حضور، سجل حضور
            attendance_type = 'check_in'
            message = f"تم تسجيل حضور: {employee['name']} في {current_time_str}"
        
        # إضافة تسجيل الحضور
        attendance_data = {
            'employee_id': employee_id,
            'check_time': current_time_str,
            'date': current_date,
            'type': attendance_type,
            'notes': f'QR Code scan by {admin_user["username"]}'
        }
        
        if db_manager.add_attendance(attendance_data):
            return jsonify({
                'success': True,
                'message': message,
                'employee': {
                    'name': employee['name'],
                    'code': employee['employee_code'],
                    'department': employee.get('department', ''),
                    'type': attendance_type,
                    'time': current_time_str
                }
            }), 200
        else:
            return jsonify({'success': False, 'error': 'فشل في تسجيل الحضور'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': f'خطأ في معالجة الرمز: {str(e)}'}), 500


# --- بدء تشغيل الخادم ---
if __name__ == '__main__':
    print("--- Starting Web App Server (Local SQLite Mode) ---")
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5000')), debug=DEBUG_MODE)
