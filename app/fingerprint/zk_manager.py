from zk import ZK, const

class ZKManager:
    def __init__(self, ip, port=4370, timeout=5, password=0):
        self.ip = ip
        self.port = port
        self.timeout = timeout
        self.password = password
        self.zk = ZK(self.ip, port=self.port, timeout=self.timeout, password=self.password, force_udp=False, ommit_ping=False)
        self.conn = None

    def connect(self):
        """محاولة الاتصال بالجهاز."""
        try:
            self.conn = self.zk.connect()
            if self.conn:
                print(f"Successfully connected to device at {self.ip}")
                self.zk.disable_device()
                return True
        except Exception as e:
            print(f"Connection failed: {e}")
            self.conn = None # التأكد من أن الاتصال فارغ عند الFailed
            return False

    def disconnect(self):
        """قطع الاتصال بالجهاز."""
        try:
            if self.conn:
                self.zk.enable_device()
                self.zk.disconnect()
                print("Disconnected from device.")
        except Exception as e:
            print(f"Disconnection failed: {e}")
        finally:
            self.conn = None

    def get_attendance(self):
        """سحب سجلات الحضور والانصراف من الجهاز."""
        if not self.conn:
            print("Not connected to a device.")
            return []
        try:
            # سحب سجلات الحضور
            return self.zk.get_attendance()
        except Exception as e:
            print(f"Failed to get attendance logs: {e}")
            return []
        finally:
            # التأكد من إعادة تفعيل الجهاز دائمًا
            if self.conn:
                self.zk.enable_device()

    def get_users(self):
        """سحب بيانات المستخدمين المسجلين على الجهاز."""
        if not self.conn:
            print("Not connected to a device.")
            return []
        try:
            return self.zk.get_users()
        except Exception as e:
            print(f"Failed to get users: {e}")
            return []

    def clear_attendance(self):
        """مسح سجلات الحضور من ذاكرة الجهاز."""
        if not self.conn:
            print("Not connected to a device.")
            return
        try:
            self.zk.clear_attendance()
            print("Attendance logs cleared from device.")
        except Exception as e:
            print(f"Failed to clear attendance: {e}")


    def enroll_fingerprint(self, user_id):
        """
        يبدأ عملية تسجيل بصمة جديدة لمستخدم على الجهاز.
        هذه الدالة تفاعلية وتنتظر وضع الإصبع.
        
        :param user_id: كود الموظف (يجب أن يكون رقمًا أو نصًا قصيرًا).
        :return: قالب البصمة عند النجاح، أو None عند الFailed.
        """
        if not self.conn:
            print("Not connected to a device.")
            raise ConnectionError("Not connected to a device.")

        try:
            # uid يجب أن يكون سلسلة نصية
            uid = str(user_id)
            
            # ضع الجهاز في وضع التسجيل
            # enroll_user هي دالة generator في pyzk
            enrollment_generator = self.zk.enroll_user(uid=uid)
            
            fingerprint_template = None
            for step in enrollment_generator:
                if step == 1:
                    print(f"Enrollment started for user {uid}. Please place a finger.")
                    # هنا يمكن للواجهة عرض رسالة للمستخدم
                elif step == 2:
                    print("Fingerprint captured. Please place the same finger again.")
                elif step == 3:
                    print("Fingerprint captured again. Please place the same finger a third time.")
                elif isinstance(step, tuple) and len(step) > 1:
                    # step هو tuple يحتوي على (finger_id, template) عند النجاح
                    fingerprint_template = step[1] # نحصل على قالب البصمة
                    print("Enrollment successful!")
                    break # نخرج من الحلقة عند النجاح
            
            if fingerprint_template:
                return fingerprint_template
            else:
                print("Enrollment failed or was canceled.")
                return None

        except Exception as e:
            print(f"An error occurred during enrollment: {e}")
            raise e # نمرر الError للأعلى لتعالجه الواجهة