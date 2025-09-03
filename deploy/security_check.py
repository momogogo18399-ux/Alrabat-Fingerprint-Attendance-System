#!/usr/bin/env python3
"""
Script to check system security settings
Should be run after deployment to verify correct settings
"""

import os
import sys
import subprocess
import json
from pathlib import Path
import time

# Try to import requests, with fallback for environments where it's not installed
try:
    import requests  # type: ignore
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: 'requests' module not found. Some security checks will be skipped.")
    print("To install: pip install requests")

def print_status(message: str, status: str = "INFO"):
    """Print message with colored status"""
    colors = {
        "INFO": "\033[94m",    # Blue
        "SUCCESS": "\033[92m", # Green
        "WARNING": "\033[93m", # Yellow
        "ERROR": "\033[91m",   # Red
        "RESET": "\033[0m"     # Reset
    }
    print(f"{colors.get(status, colors['INFO'])}[{status}]{colors['RESET']} {message}")

def check_file_permissions():
    """Check file permissions"""
    print_status("Checking file permissions...", "INFO")
    
    # Cross-platform file paths
    if os.name == 'nt':  # Windows
        critical_files = [
            os.path.join(os.getcwd(), ".env"),
            os.path.join(os.getcwd(), "attendance.db"),
            os.path.join(os.getcwd(), "deploy", "github_token.txt")
        ]
    else:  # Unix/Linux
        critical_files = [
            "/opt/attendance/.env",
            "/opt/attendance/attendance.db",
            "/opt/attendance/github_token.txt"
        ]
    
    for file_path in critical_files:
        if os.path.exists(file_path):
            if os.name == 'nt':  # Windows
                # On Windows, just check if file exists and is readable
                try:
                    with open(file_path, 'r') as f:
                        f.read(1)  # Try to read one character
                    print_status(f"✓ {file_path} is accessible", "SUCCESS")
                except PermissionError:
                    print_status(f"Warning: {file_path} is not accessible", "WARNING")
                except Exception as e:
                    print_status(f"Warning: {file_path} has issues: {e}", "WARNING")
            else:  # Unix/Linux
                stat = os.stat(file_path)
                mode = oct(stat.st_mode)[-3:]
                owner = stat.st_uid
                
                if mode != "600" and mode != "640":
                    print_status(f"Warning: {file_path} has permissions {mode}, should be 600 or 640", "WARNING")
                else:
                    print_status(f"✓ {file_path} has correct permissions: {mode}", "SUCCESS")
        else:
            print_status(f"File not found: {file_path}", "WARNING")

def check_ssl_certificate(domain: str):
    """Check SSL certificate"""
    if not REQUESTS_AVAILABLE:
        print_status("Skipping SSL certificate check - requests module not available", "WARNING")
        return
        
    print_status(f"Checking SSL certificate for {domain}...", "INFO")
    
    try:
        response = requests.get(f"https://{domain}/healthz", timeout=10, verify=True)
        if response.status_code == 200:
            print_status(f"✓ SSL certificate is valid for {domain}", "SUCCESS")
        else:
            print_status(f"Warning: SSL works but health check returned {response.status_code}", "WARNING")
    except requests.exceptions.SSLError:
        print_status(f"✗ SSL certificate error for {domain}", "ERROR")
    except requests.exceptions.RequestException as e:
        print_status(f"✗ Cannot reach {domain}: {e}", "ERROR")

def check_firewall():
    """Check firewall settings"""
    print_status("Checking firewall settings...", "INFO")
    
    if os.name == 'nt':  # Windows
        try:
            # Check Windows Firewall status
            result = subprocess.run(["netsh", "advfirewall", "show", "allprofiles"], capture_output=True, text=True)
            if result.returncode == 0:
                if "ON" in result.stdout:
                    print_status("✓ Windows Firewall is active", "SUCCESS")
                else:
                    print_status("✗ Windows Firewall is not active", "ERROR")
            else:
                print_status("Warning: Could not check Windows Firewall status", "WARNING")
        except Exception as e:
            print_status(f"Warning: Could not check firewall: {e}", "WARNING")
    else:  # Unix/Linux
        try:
            result = subprocess.run(["ufw", "status"], capture_output=True, text=True)
            if "Status: active" in result.stdout:
                print_status("✓ UFW firewall is active", "SUCCESS")
                
                # Check open ports
                if "22/tcp" in result.stdout:
                    print_status("✓ SSH port (22) is open", "SUCCESS")
                else:
                    print_status("Warning: SSH port (22) might be closed", "WARNING")
                    
                if "80/tcp" in result.stdout or "443/tcp" in result.stdout:
                    print_status("✓ HTTP/HTTPS ports are open", "SUCCESS")
                else:
                    print_status("Warning: HTTP/HTTPS ports might be closed", "WARNING")
            else:
                print_status("✗ UFW firewall is not active", "ERROR")
        except FileNotFoundError:
            print_status("Warning: UFW not installed", "WARNING")

def check_service_status():
    """Check service status"""
    print_status("Checking service status...", "INFO")
    
    if os.name == 'nt':  # Windows
        # Check Windows services
        services = ["MpsSvc", "Spooler"]  # Windows Firewall and Print Spooler as examples
        for service in services:
            try:
                result = subprocess.run(["sc", "query", service], capture_output=True, text=True)
                if "RUNNING" in result.stdout:
                    print_status(f"✓ {service} service is running", "SUCCESS")
                else:
                    print_status(f"⚠ {service} service is not running", "WARNING")
            except Exception as e:
                print_status(f"Error checking {service}: {e}", "ERROR")
    else:  # Unix/Linux
        services = ["attendance", "nginx", "postgresql"]
        
        for service in services:
            try:
                result = subprocess.run(["systemctl", "is-active", service], capture_output=True, text=True)
                if result.stdout.strip() == "active":
                    print_status(f"✓ {service} service is active", "SUCCESS")
                else:
                    print_status(f"✗ {service} service is not active: {result.stdout.strip()}", "ERROR")
            except Exception as e:
                print_status(f"Error checking {service}: {e}", "ERROR")

def check_database_connection():
    """Check database connection"""
    print_status("Checking database connection...", "INFO")
    
    if os.name == 'nt':  # Windows
        try:
            # Try to import and test database connection directly
            import sys
            sys.path.insert(0, os.path.join(os.getcwd(), 'app'))
            
            try:
                from database.database_manager import DatabaseManager
                db = DatabaseManager()
                print_status("✓ Database connection successful", "SUCCESS")
                
                # Try to get database type
                try:
                    db_type = "PostgreSQL" if db.is_postgres else "SQLite"
                    print_status(f"✓ Database type: {db_type}", "SUCCESS")
                except Exception:
                    print_status("✓ Database connected (type unknown)", "SUCCESS")
                    
            except ImportError as e:
                print_status(f"✗ Could not import database module: {e}", "ERROR")
            except Exception as e:
                print_status(f"✗ Database connection failed: {e}", "ERROR")
                print_status("   Check database configuration in .env file", "INFO")
                
        except Exception as e:
            print_status(f"Error checking database: {e}", "ERROR")
    else:  # Unix/Linux
        try:
            # Attempt database connection
            result = subprocess.run([
                "sudo", "-u", "attendance", "bash", "-c",
                "cd /opt/attendance && source .venv/bin/activate && python -c 'from app.database.database_manager import DatabaseManager; db = DatabaseManager(); print(\"Connected\")'"
            ], capture_output=True, text=True, timeout=30)
            
            if "Connected" in result.stdout:
                print_status("✓ Database connection successful", "SUCCESS")
                
                # محاولة الحصول على Information إضافية
                try:
                    info_result = subprocess.run([
                        "sudo", "-u", "attendance", "bash", "-c",
                        "cd /opt/attendance && source .venv/bin/activate && python -c 'from app.database.database_manager import DatabaseManager; db = DatabaseManager(); print(f\"DB Type: {\"PostgreSQL\" if db.is_postgres else \"SQLite\"}\")'"
                    ], capture_output=True, text=True, timeout=10)
                    
                    if "DB Type:" in info_result.stdout:
                        db_type = info_result.stdout.split("DB Type:")[1].strip()
                        print_status(f"✓ Database type: {db_type}", "SUCCESS")
                except Exception:
                    pass
                    
            else:
                print_status(f"✗ Database connection failed: {result.stderr}", "ERROR")
                print_status("   Check database configuration in .env file", "INFO")
        except subprocess.TimeoutExpired:
            print_status("✗ Database connection timeout", "ERROR")
        except Exception as e:
            print_status(f"Error checking database: {e}", "ERROR")

def check_system_resources():
    """التحقق من موارد النظام"""
    print_status("Checking system resources...", "INFO")
    
    try:
        if os.name == 'nt':  # Windows
            # Windows system resource check
            import psutil
            
            # Memory usage
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024**3)
            used_gb = memory.used / (1024**3)
            print_status(f"✓ Memory usage: {used_gb:.1f}GB/{total_gb:.1f}GB ({memory.percent}%)", "SUCCESS")
            
            # Disk usage
            disk = psutil.disk_usage(os.getcwd())
            total_gb = disk.total / (1024**3)
            used_gb = disk.used / (1024**3)
            print_status(f"✓ Disk usage: {used_gb:.1f}GB/{total_gb:.1f}GB ({disk.percent}%)", "SUCCESS")
            
        else:  # Unix/Linux
            # فحص استخدام الذاكرة
            memory_result = subprocess.run(["free", "-h"], capture_output=True, text=True)
            if memory_result.returncode == 0:
                lines = memory_result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    mem_info = lines[1].split()
                    if len(mem_info) >= 3:
                        total = mem_info[1]
                        used = mem_info[2]
                        print_status(f"✓ Memory usage: {used}/{total}", "SUCCESS")
            
            # فحص مساحة القرص
            disk_result = subprocess.run(["df", "-h", "/opt/attendance"], capture_output=True, text=True)
            if disk_result.returncode == 0:
                lines = disk_result.stdout.strip().split('\n')
                if len(lines) >= 2:
                    disk_info = lines[1].split()
                    if len(disk_info) >= 5:
                        usage = disk_info[4]
                        print_status(f"✓ Disk usage: {usage}", "SUCCESS")
                    
    except ImportError:
        print_status("Warning: psutil not available for Windows resource check", "WARNING")
    except Exception as e:
        print_status(f"Error checking system resources: {e}", "WARNING")

def check_logs():
    """التحقق من السجلات للأخطاء"""
    print_status("Checking application logs...", "INFO")
    
    if os.name == 'nt':  # Windows
        try:
            # Check Windows Event Logs for errors
            result = subprocess.run([
                "powershell", "Get-EventLog", "-LogName", "Application", "-EntryType", "Error", "-Newest", "10"
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                error_count = result.stdout.count('Error')
                if error_count > 0:
                    print_status(f"⚠ Found {error_count} recent errors in Windows Event Log", "WARNING")
                else:
                    print_status("✓ No recent errors found in Windows Event Log", "SUCCESS")
            else:
                print_status("⚠ Could not read Windows Event Log", "WARNING")
                
        except subprocess.TimeoutExpired:
            print_status("⚠ Log check timeout", "WARNING")
        except Exception as e:
            print_status(f"Error checking logs: {e}", "WARNING")
    else:  # Unix/Linux
        try:
            # فحص سجلات الخدمة
            log_result = subprocess.run([
                "journalctl", "-u", "attendance", "--no-pager", "-n", "50"
            ], capture_output=True, text=True, timeout=10)
            
            if log_result.returncode == 0:
                log_content = log_result.stdout.lower()
                error_count = log_content.count('error')
                warning_count = log_content.count('warning')
                
                if error_count > 0:
                    print_status(f"⚠ Found {error_count} errors in recent logs", "WARNING")
                else:
                    print_status("✓ No recent errors found in logs", "SUCCESS")
                    
                if warning_count > 0:
                    print_status(f"⚠ Found {warning_count} warnings in recent logs", "WARNING")
            else:
                print_status("⚠ Could not read service logs", "WARNING")
                
        except subprocess.TimeoutExpired:
            print_status("⚠ Log check timeout", "WARNING")
        except Exception as e:
            print_status(f"Error checking logs: {e}", "WARNING")

def check_backup_status():
    """التحقق من حالة النسخ الاحتياطي"""
    print_status("Checking backup status...", "INFO")
    
    # Cross-platform backup directory
    if os.name == 'nt':  # Windows
        backup_dir = os.path.join(os.getcwd(), "backups")
    else:  # Unix/Linux
        backup_dir = "/opt/attendance/backups"
    
    if os.path.exists(backup_dir):
        try:
            # الSearch عن أحدث نسخة احتياطية
            backup_files = [f for f in os.listdir(backup_dir) if f.endswith('.sql') or f.endswith('.tar.gz')]
            if backup_files:
                latest_backup = max(backup_files, key=lambda x: os.path.getctime(os.path.join(backup_dir, x)))
                backup_time = os.path.getctime(os.path.join(backup_dir, latest_backup))
                backup_age_hours = (time.time() - backup_time) / 3600
                
                if backup_age_hours < 24:
                    print_status(f"✓ Recent backup found: {latest_backup} ({backup_age_hours:.1f}h ago)", "SUCCESS")
                else:
                    print_status(f"⚠ Old backup found: {latest_backup} ({backup_age_hours:.1f}h ago)", "WARNING")
            else:
                print_status("⚠ No backup files found", "WARNING")
        except Exception as e:
            print_status(f"Error checking backups: {e}", "WARNING")
    else:
        print_status("⚠ Backup directory not found", "WARNING")

def check_update_api(domain: str):
    """التحقق من API الUpdateات"""
    if not REQUESTS_AVAILABLE:
        print_status("Skipping update API check - requests module not available", "WARNING")
        return
        
    print_status(f"Checking update API at {domain}...", "INFO")
    
    try:
        response = requests.get(f"https://{domain}/api/app-version", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print_status(f"✓ Update API is working, version: {data.get('version', 'unknown')}", "SUCCESS")
            
            # التحقق من headers الأمان
            headers = response.headers
            if 'X-Frame-Options' in headers:
                print_status("✓ Security headers are present", "SUCCESS")
            else:
                print_status("Warning: Security headers might be missing", "WARNING")
        else:
            print_status(f"✗ Update API returned status {response.status_code}", "ERROR")
    except Exception as e:
        print_status(f"✗ Cannot reach update API: {e}", "ERROR")

def check_environment_variables():
    """التحقق من متغيرات البيئة"""
    print_status("Checking environment variables...", "INFO")
    
    # Cross-platform env file path
    if os.name == 'nt':  # Windows
        env_file = os.path.join(os.getcwd(), ".env")
    else:  # Unix/Linux
        env_file = "/opt/attendance/.env"
    
    if not os.path.exists(env_file):
        print_status("✗ .env file not found", "ERROR")
        return
    
    required_vars = [
        "FLASK_DEBUG",
        "DATABASE_URL",
        "UPDATE_SERVER_URL",
        "GITHUB_OWNER",
        "GITHUB_REPO",
        "SECRET_KEY"
    ]
    
    with open(env_file, 'r') as f:
        env_content = f.read()
    
    for var in required_vars:
        if f"{var}=" in env_content:
            print_status(f"✓ {var} is set", "SUCCESS")
        else:
            print_status(f"Warning: {var} is not set", "WARNING")

def main():
    """الدالة الرئيسية"""
    print_status("Starting comprehensive security check for Attendance System...", "INFO")
    print()
    
    # Check if requests module is available
    if not REQUESTS_AVAILABLE:
        print_status("Note: Some checks will be skipped due to missing 'requests' module", "WARNING")
        print_status("To install missing dependencies, run: python deploy/install_dependencies.py", "INFO")
        print()
    
    # الحصول على النطاق من المعاملات أو استخدام localhost
    domain = sys.argv[1] if len(sys.argv) > 1 else "localhost"
    
    # التحقق من الصلاحيات (cross-platform)
    try:
        # Unix/Linux systems
        if hasattr(os, 'geteuid'):
            if os.geteuid() != 0:
                print_status("Warning: Running without root privileges, some checks may fail", "WARNING")
        else:
            # Windows systems - check if running as administrator
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                print_status("Warning: Running without administrator privileges, some checks may fail", "WARNING")
    except Exception:
        print_status("Warning: Could not determine privileges, some checks may fail", "WARNING")
    print()
    
    # تشغيل جميع الفحوصات الأساسية
    check_file_permissions()
    print()
    
    check_ssl_certificate(domain)
    print()
    
    check_firewall()
    print()
    
    check_service_status()
    print()
    
    check_database_connection()
    print()
    
    check_update_api(domain)
    print()
    
    check_environment_variables()
    print()
    
    # تشغيل الفحوصات الإضافية
    check_system_resources()
    print()
    
    check_logs()
    print()
    
    check_backup_status()
    print()
    
    # ملخص النتائج
    print_status("=" * 60, "INFO")
    print_status("Security check completed!", "SUCCESS")
    print_status("Review any warnings or errors above and fix them if needed.", "INFO")
    print_status("=" * 60, "INFO")
    
    # نصائح إضافية
    print_status("Additional recommendations:", "INFO")
    if os.name == 'nt':  # Windows
        print_status("1. Regularly update Windows: Check for updates in Settings", "INFO")
        print_status("2. Monitor logs: Use Event Viewer (eventvwr.msc)", "INFO")
        print_status("3. Set up automated backups", "INFO")
        print_status("4. Review firewall rules: Windows Defender Firewall", "INFO")
        print_status("5. Check SSL certificate expiry: Use certmgr.msc", "INFO")
    else:  # Unix/Linux
        print_status("1. Regularly update the system: sudo apt update && sudo apt upgrade", "INFO")
        print_status("2. Monitor logs: sudo journalctl -u attendance -f", "INFO")
        print_status("3. Set up automated backups", "INFO")
        print_status("4. Review firewall rules: sudo ufw status", "INFO")
        print_status("5. Check SSL certificate expiry: sudo certbot certificates", "INFO")

if __name__ == "__main__":
    main()
