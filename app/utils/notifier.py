import os
import socket
from http.server import BaseHTTPRequestHandler, HTTPServer
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from typing import Optional

# المنفذ الذي سيستمع عليه تطبيق سطح المكتب. قابل للضبط عبر .env
NOTIFIER_PORT = int(os.getenv('NOTIFIER_PORT', '8989'))
NOTIFIER_HOST = os.getenv('NOTIFIER_HOST', 'localhost')

class NotificationHandler(BaseHTTPRequestHandler):
    """
    معالج الطلبات الذي يستجيب لطلبات الUpdate.
    """
    # نمرر إشارة PyQt كوسيط
    def __init__(self, request, client_address, server, signal_emitter):
        self.signal_emitter = signal_emitter
        super().__init__(request, client_address, server)

    def do_GET(self):
        """
        عند استقبال أي طلب GET، قم بإصدار الإشارة.
        """
        if self.path == '/notify':
            print("[Notifier] Received update signal. Emitting...")
            self.signal_emitter.emit() # إصدار الإشارة لUpdate الواجهة
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'Not Found')

class NotifierThread(QThread):
    """
    خيط (Thread) مخصص لتشغيل خادم الإشعارات في الخلفية دون تجميد الواجهة الرئيسية.
    """
    # نمرر الإشارة التي سيتم إصدارها
    update_signal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.httpd: Optional[HTTPServer] = None

    def run(self):
        # دالة لإنشاء معالج طلبات مخصص مع تمرير الإشارة
        def handler(*args, **kwargs):
            return NotificationHandler(*args, **kwargs, signal_emitter=self.update_signal)

        try:
            class ReusableHTTPServer(HTTPServer):
                allow_reuse_address = True

            with ReusableHTTPServer((NOTIFIER_HOST, NOTIFIER_PORT), handler) as httpd:
                self.httpd = httpd
                print(f"[Notifier] Starting server on http://{NOTIFIER_HOST}:{NOTIFIER_PORT}")
                httpd.serve_forever()
        except OSError as e:
            # هذا يحدث غالبًا إذا كان المنفذ مستخدمًا بالفعل
            print(f"[Notifier] ERROR: Could not start server on port {NOTIFIER_PORT}. {e}")
        except Exception as e:
            print(f"[Notifier] An unexpected error occurred: {e}")
        finally:
            self.httpd = None

    def stop(self):
        """إيقاف الخادم الخلفي بأمان."""
        try:
            if self.httpd is not None:
                self.httpd.shutdown()
        except Exception as e:
            print(f"[Notifier] Error during shutdown: {e}")