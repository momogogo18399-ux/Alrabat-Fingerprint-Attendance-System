import os
import tempfile
import shutil
import subprocess
import platform
from typing import Optional, Tuple, Dict

import requests


DEFAULT_SERVER_URL = os.getenv('UPDATE_SERVER_URL', 'http://localhost:5000')


def get_current_version() -> str:
    try:
        from app.version import APP_VERSION
        return APP_VERSION
    except Exception:
        return "1.0.0"


def parse_version(version_str: str) -> Tuple[int, int, int]:
    try:
        parts = version_str.strip().split('.')
        major = int(parts[0]) if len(parts) > 0 else 0
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        return major, minor, patch
    except Exception:
        return 0, 0, 0


def is_newer_version(latest: str, current: str) -> bool:
    return parse_version(latest) > parse_version(current)


def fetch_latest_info(server_url: Optional[str] = None, timeout_sec: float = 3.0) -> Optional[Dict]:
    base_url = (server_url or DEFAULT_SERVER_URL).rstrip('/')
    url = f"{base_url}/api/app-version?platform=windows&channel=stable"
    try:
        resp = requests.get(url, timeout=timeout_sec)
        if resp.status_code == 200:
            return resp.json()
    except requests.RequestException:
        pass
    return None


def download_file(url: str, suggested_name: str = "AttendanceAdminInstaller.exe", timeout_sec: float = 30.0) -> Optional[str]:
    try:
        with requests.get(url, stream=True, timeout=timeout_sec) as r:
            r.raise_for_status()
            fd, tmp_path = tempfile.mkstemp(prefix="attendance_update_", suffix="_" + suggested_name)
            os.close(fd)
            with open(tmp_path, 'wb') as f:
                shutil.copyfileobj(r.raw, f)
            return tmp_path
    except requests.RequestException:
        return None


def run_windows_installer(installer_path: str, silent: bool = True) -> bool:
    if platform.system().lower() != 'windows':
        return False
    try:
        args = [installer_path]
        if silent:
            # Inno Setup common silent flags
            args.extend(["/VERYSILENT", "/NORESTART"])
        subprocess.Popen(args, shell=False)
        return True
    except Exception:
        return False


