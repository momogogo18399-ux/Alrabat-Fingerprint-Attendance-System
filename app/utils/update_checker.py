import os
import tempfile
import shutil
import subprocess
import platform
from typing import Optional, Tuple, Dict
import logging

import requests

# تحسين إعدادات الخادم الافتراضية
DEFAULT_SERVER_URL = os.getenv('UPDATE_SERVER_URL', 'https://attendance.yourdomain.com')
FALLBACK_SERVER_URL = os.getenv('FALLBACK_SERVER_URL', 'http://localhost:5000')

# إعدادات إضافية للUpdateات
UPDATE_TIMEOUT = float(os.getenv('UPDATE_TIMEOUT', '10.0'))
DOWNLOAD_TIMEOUT = float(os.getenv('DOWNLOAD_TIMEOUT', '60.0'))
MAX_RETRIES = int(os.getenv('UPDATE_MAX_RETRIES', '3'))

logger = logging.getLogger(__name__)

def get_current_version() -> str:
    try:
        from app.version import APP_VERSION
        return APP_VERSION
    except Exception as e:
        logger.error(f"Failed to get current version: {e}")
        return "1.0.0"

def parse_version(version_str: str) -> Tuple[int, int, int]:
    try:
        parts = version_str.strip().split('.')
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return major, minor, patch
    except Exception as e:
        logger.error(f"Failed to parse version {version_str}: {e}")
        return 0, 0, 0

def is_newer_version(latest: str, current: str) -> bool:
    return parse_version(latest) > parse_version(current)

def fetch_latest_info(server_url: Optional[str] = None, timeout_sec: float = UPDATE_TIMEOUT) -> Optional[Dict]:
    """
    يحاول جلب Information الUpdate من الخادم الرئيسي، وإذا Failed يحاول الخادم الاحتياطي
    """
    # Return None to disable update checks and prevent crashes
    return None
    
    urls_to_try = []
    
    if server_url:
        urls_to_try.append(server_url.rstrip('/'))
    else:
        urls_to_try.extend([
            DEFAULT_SERVER_URL.rstrip('/'),
            FALLBACK_SERVER_URL.rstrip('/')
        ])
    
    for base_url in urls_to_try:
        url = f"{base_url}/api/app-version?platform=windows&channel=stable"
        try:
            logger.info(f"Trying to fetch update info from: {url}")
            resp = requests.get(url, timeout=timeout_sec, verify=True)
            if resp.status_code == 200:
                data = resp.json()
                logger.info(f"Successfully fetched update info: {data.get('version', 'unknown')}")
                return data
            else:
                logger.warning(f"Server returned status {resp.status_code} for {url}")
        except requests.RequestException as e:
            logger.warning(f"Failed to fetch from {url}: {e}")
            continue
    
    logger.error("All update servers failed")
    return None

def download_file(url: str, suggested_name: str = "AttendanceAdminInstaller.exe", timeout_sec: float = DOWNLOAD_TIMEOUT) -> Optional[str]:
    """
    تحميل ملف الUpdate مع إدارة أفضل للأخطاء والتقدم
    """
    try:
        logger.info(f"Starting download from: {url}")
        
        # التحقق من حجم الملف أولاً
        head_resp = requests.head(url, timeout=10.0, verify=True)
        if head_resp.status_code != 200:
            logger.error(f"Failed to get file info: {head_resp.status_code}")
            return None
            
        content_length = head_resp.headers.get('content-length')
        if content_length:
            file_size = int(content_length)
            logger.info(f"File size: {file_size / (1024*1024):.1f} MB")
        
        # تحميل الملف
        with requests.get(url, stream=True, timeout=timeout_sec, verify=True) as r:
            r.raise_for_status()
            
            fd, tmp_path = tempfile.mkstemp(prefix="attendance_update_", suffix="_" + suggested_name)
            os.close(fd)
            
            with open(tmp_path, 'wb') as f:
                downloaded = 0
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # تسجيل التقدم كل 1MB
                        if downloaded % (1024*1024) == 0:
                            logger.info(f"Downloaded: {downloaded / (1024*1024):.1f} MB")
            
            logger.info(f"Download completed: {tmp_path}")
            return tmp_path
            
    except requests.RequestException as e:
        logger.error(f"Download failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during download: {e}")
        return None

def run_windows_installer(installer_path: str, silent: bool = True) -> bool:
    if platform.system().lower() != 'windows':
        logger.warning("Installer can only run on Windows")
        return False
        
    try:
        logger.info(f"Starting installer: {installer_path}")
        args = [installer_path]
        if silent:
            # Inno Setup common silent flags
            args.extend(["/VERYSILENT", "/NORESTART", "/SUPPRESSMSGBOXES"])
        
        # تشغيل المثبت في عملية منفصلة
        process = subprocess.Popen(args, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # انتظار قليل للتأكد من بدء المثبت
        import time
        time.sleep(2)
        
        if process.poll() is None:
            logger.info("Installer started successfully")
            return True
        else:
            logger.error(f"Installer failed to start, exit code: {process.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to run installer: {e}")
        return False

def verify_installer_file(file_path: str) -> bool:
    """
    التحقق من صحة ملف المثبت
    """
    try:
        if not os.path.exists(file_path):
            return False
            
        # التحقق من حجم الملف (يجب أن يكون أكبر من 1MB)
        file_size = os.path.getsize(file_path)
        if file_size < 1024 * 1024:
            logger.warning(f"Installer file too small: {file_size} bytes")
            return False
            
        # التحقق من امتداد الملف
        if not file_path.lower().endswith('.exe'):
            logger.warning("Installer file is not an .exe file")
            return False
            
        logger.info(f"Installer file verified: {file_size / (1024*1024):.1f} MB")
        return True
        
    except Exception as e:
        logger.error(f"Failed to verify installer: {e}")
        return False


