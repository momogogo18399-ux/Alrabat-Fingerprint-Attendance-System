# دليل النشر على VPS - نظام الحضور والانصراف

## نظرة عامة

هذا الدليل يوضح كيفية نشر نظام الحضور والانصراف على VPS مع دعم التحديثات التلقائية وقاعدة البيانات المشتركة.

## المتطلبات

- VPS يعمل بـ Ubuntu 20.04 أو أحدث
- نطاق أو IP ثابت
- حساب GitHub (للتحديثات)

## الطريقة السريعة (موصى بها)

### 1. إعداد VPS تلقائي

```bash
# تشغيل سكريبت التثبيت التلقائي
curl -fsSL https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/deploy/install_vps.sh | bash -s -- \
  --repo-url https://github.com/YOUR_USER/YOUR_REPO.git \
  --domain your-domain.com \
  --db-url "postgresql://attendance:strongpass@127.0.0.1:5432/attendance" \
  --github-owner YOUR_GITHUB_USERNAME \
  --github-repo YOUR_REPO_NAME
```

### 2. إعداد SSL (HTTPS)

```bash
# تثبيت شهادة SSL مجانية
sudo certbot --nginx -d your-domain.com --non-interactive --agree-tos --email your-email@example.com
```

### 3. إعداد GitHub Token

```bash
# إنشاء token في GitHub: Settings > Developer settings > Personal access tokens
# ثم إضافته إلى الخادم
sudo -u attendance bash -lc 'echo "YOUR_GITHUB_TOKEN" > /opt/attendance/github_token.txt'
```

## الطريقة اليدوية

### 1) تثبيت حزم النظام

```bash
sudo apt update && sudo apt install -y python3-pip python3-venv nginx git certbot python3-certbot-nginx postgresql postgresql-contrib
sudo adduser --system --group attendance
sudo mkdir -p /opt/attendance && sudo chown -R attendance:attendance /opt/attendance
```

### 2) إعداد قاعدة البيانات PostgreSQL

```bash
sudo -u postgres createuser attendance
sudo -u postgres createdb attendance
sudo -u postgres psql -c "ALTER USER attendance WITH PASSWORD 'strongpass';"
```

### 3) استنساخ المشروع وتثبيت التبعيات

```bash
sudo -u attendance bash -lc '
cd /opt/attendance
git clone https://github.com/YOUR_USER/YOUR_REPO.git .
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
'
```

### 4) إعداد متغيرات البيئة

```bash
sudo -u attendance bash -lc 'cat > /opt/attendance/.env <<ENV
# Flask Settings
FLASK_DEBUG=0
FLASK_ENV=production

# Database Settings
DATABASE_URL=postgresql://username:password@host:port/databasendance
SQLITE_FILE=/opt/attendance/attendance.db

# Update Server Settings
UPDATE_SERVER_URL=https://your-domain.com
FALLBACK_SERVER_URL=http://localhost:5000
UPDATE_TIMEOUT=10.0
DOWNLOAD_TIMEOUT=60.0
UPDATE_MAX_RETRIES=3

# GitHub Settings (for updates)
GITHUB_OWNER=YOUR_GITHUB_USERNAME
GITHUB_REPO=YOUR_REPO_NAME

# Public URLs
PUBLIC_BASE_URL=https://your-domain.com

# Update Configuration
UPDATE_NOTES=- تحسينات عامة وإصلاحات أخطاء.\\n- دعم التحقق التلقائي من التحديثات.\\n- تحسينات في الأداء والاستقرار.
MANDATORY_UPDATE=false
MIN_SUPPORTED_VERSION=1.0.0

# Desktop App Settings
THEME_DIR=/opt/attendance/assets/themes
NOTIFIER_HOST=localhost
NOTIFIER_PORT=8989

# Security Settings
SECRET_KEY=$(openssl rand -hex 32)
ENV'
```

### 5) إنشاء خدمة النظام

```bash
sudo tee /etc/systemd/system/attendance.service >/dev/null <<'UNIT'
[Unit]
Description=Attendance Flask app with Gunicorn
After=network.target

[Service]
User=attendance
Group=attendance
WorkingDirectory=/opt/attendance
Environment="PATH=/opt/attendance/.venv/bin"
EnvironmentFile=/opt/attendance/.env
ExecStart=/opt/attendance/.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 --timeout 120 --keep-alive 5 web_app:app
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/attendance

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now attendance
```

### 6) إعداد Nginx

```bash
sudo tee /etc/nginx/sites-available/attendance >/dev/null <<NGINX
server {
    listen 80;
    server_name your-domain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

    client_max_body_size 10m;
    client_body_timeout 60s;
    client_header_timeout 60s;

    # Health check endpoint
    location /healthz {
        proxy_pass http://127.0.0.1:8000/healthz;
        access_log off;
    }

    # API endpoints
    location /api/ {
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_pass http://127.0.0.1:8000;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }

    # Main application
    location / {
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_pass http://127.0.0.1:8000;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }

    # Static files (if any)
    location /static/ {
        alias /opt/attendance/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
NGINX

sudo ln -sf /etc/nginx/sites-available/attendance /etc/nginx/sites-enabled/attendance
sudo nginx -t && sudo systemctl reload nginx
```

## إعداد التحديثات التلقائية

### 1. إنشاء GitHub Repository

```bash
# إنشاء repository جديد على GitHub
# ثم رفع الكود إليه
git remote add origin https://github.com/YOUR_USER/YOUR_REPO.git
git push -u origin main
```

### 2. إنشاء GitHub Token

1. اذهب إلى GitHub > Settings > Developer settings > Personal access tokens
2. أنشئ token جديد مع صلاحيات `repo`
3. احفظ الـ token

### 3. بناء ونشر المثبتات

```bash
# على جهاز التطوير
python deploy/build_all.py --github-repo YOUR_USER/YOUR_REPO --token YOUR_GITHUB_TOKEN
```

### 4. اختبار التحديثات

```bash
# التحقق من API التحديثات
curl https://your-domain.com/api/app-version
```

## إدارة النظام

### مراقبة الخدمة

```bash
# حالة الخدمة
sudo systemctl status attendance

# مراقبة السجلات
sudo journalctl -u attendance -f

# إعادة تشغيل الخدمة
sudo systemctl restart attendance
```

### التحديثات

```bash
# تحديث الكود
sudo -u attendance bash -lc '
cd /opt/attendance
git pull
source .venv/bin/activate
pip install -r requirements.txt
'

# إعادة تشغيل الخدمة
sudo systemctl restart attendance
```

### النسخ الاحتياطي

```bash
# نسخ احتياطي لقاعدة البيانات
sudo -u postgres pg_dump attendance > backup_$(date +%Y%m%d_%H%M%S).sql

# نسخ احتياطي للملفات
sudo tar -czf attendance_backup_$(date +%Y%m%d_%H%M%S).tar.gz /opt/attendance
```

## استكشاف الأخطاء

### مشاكل شائعة

1. **الخدمة لا تبدأ**
   ```bash
   sudo journalctl -u attendance --no-pager
   ```

2. **مشاكل قاعدة البيانات**
   ```bash
   sudo -u postgres psql -d attendance -c "SELECT version();"
   ```

3. **مشاكل Nginx**
   ```bash
   sudo nginx -t
   sudo tail -f /var/log/nginx/error.log
   ```

### اختبار الاتصال

```bash
# اختبار الخدمة المحلية
curl http://127.0.0.1:8000/healthz

# اختبار Nginx
curl http://your-domain.com/healthz

# اختبار API التحديثات
curl https://your-domain.com/api/app-version
```

## الأمان

### إعدادات الأمان الموصى بها

1. **جدار الحماية**
   ```bash
   sudo ufw allow ssh
   sudo ufw allow 'Nginx Full'
   sudo ufw enable
   ```

2. **تحديث النظام**
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

3. **مراقبة السجلات**
   ```bash
   sudo tail -f /var/log/nginx/access.log
   sudo journalctl -u attendance -f
   ```

## الدعم

للمساعدة أو الإبلاغ عن مشاكل:
- افتح issue على GitHub repository
- راجع السجلات: `sudo journalctl -u attendance -f`
- تحقق من حالة الخدمة: `sudo systemctl status attendance`



