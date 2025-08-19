#!/usr/bin/env bash
set -euo pipefail

# Usage (Ubuntu):
#   curl -fsSL https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/deploy/install_vps.sh | bash -s -- \
#     --repo-url https://github.com/YOUR_USER/YOUR_REPO.git \
#     --domain YOUR_DOMAIN_OR_IP \
#     --db-url "postgresql://attendance:strongpass@127.0.0.1:5432/attendance" \
#     --github-owner YOUR_GITHUB_USERNAME \
#     --github-repo YOUR_REPO_NAME

REPO_URL=""
DOMAIN_OR_IP=""
DB_URL=""
GITHUB_OWNER=""
GITHUB_REPO=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-url) REPO_URL="$2"; shift 2 ;;
    --domain) DOMAIN_OR_IP="$2"; shift 2 ;;
    --db-url) DB_URL="$2"; shift 2 ;;
    --github-owner) GITHUB_OWNER="$2"; shift 2 ;;
    --github-repo) GITHUB_REPO="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$REPO_URL" || -z "$DOMAIN_OR_IP" ]]; then
  echo "Missing required args. Example: --repo-url https://github.com/you/repo.git --domain your.ip" >&2
  exit 1
fi

echo "[1/7] Installing packages..."
sudo apt update
sudo apt install -y python3-pip python3-venv nginx git certbot python3-certbot-nginx

echo "[2/7] Creating service user and directory..."
sudo adduser --system --group attendance || true
sudo mkdir -p /opt/attendance
sudo chown -R attendance:attendance /opt/attendance

echo "[3/7] Cloning repo and creating venv..."
sudo -u attendance bash -lc "cd /opt/attendance && git clone '$REPO_URL' ."
sudo -u attendance bash -lc "cd /opt/attendance && python3 -m venv .venv && source .venv/bin/activate && pip install --upgrade pip setuptools wheel && pip install -r requirements.txt"

echo "[4/7] Writing .env with enhanced settings..."
sudo -u attendance bash -lc "cat > /opt/attendance/.env <<ENV
# Flask Settings
FLASK_DEBUG=0
FLASK_ENV=production

# Database Settings
${DB_URL:+DATABASE_URL=$DB_URL}
SQLITE_FILE=/opt/attendance/attendance.db

# Update Server Settings
UPDATE_SERVER_URL=https://${DOMAIN_OR_IP}
FALLBACK_SERVER_URL=http://localhost:5000
UPDATE_TIMEOUT=10.0
DOWNLOAD_TIMEOUT=60.0
UPDATE_MAX_RETRIES=3

# GitHub Settings (for updates)
${GITHUB_OWNER:+GITHUB_OWNER=$GITHUB_OWNER}
${GITHUB_REPO:+GITHUB_REPO=$GITHUB_REPO}

# Public URLs
PUBLIC_BASE_URL=https://${DOMAIN_OR_IP}

# Update Configuration
UPDATE_NOTES=- تحسينات عامة وإصلاحات أخطاء.\n- دعم التحقق التلقائي من التحديثات.\n- تحسينات في الأداء والاستقرار.
MANDATORY_UPDATE=false
MIN_SUPPORTED_VERSION=1.0.0

# Desktop App Settings
THEME_DIR=/opt/attendance/assets/themes
NOTIFIER_HOST=localhost
NOTIFIER_PORT=8989

# Security Settings
SECRET_KEY=$(openssl rand -hex 32)
ENV"

echo "[5/7] Creating systemd service..."
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

echo "[6/7] Configuring Nginx with security headers..."
sudo tee /etc/nginx/sites-available/attendance >/dev/null <<NGINX
server {
    listen 80;
    server_name ${DOMAIN_OR_IP};

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
sudo nginx -t
sudo systemctl reload nginx

echo "[7/7] Setting up SSL certificate (optional)..."
if command -v certbot &> /dev/null; then
    echo "To enable HTTPS, run: sudo certbot --nginx -d ${DOMAIN_OR_IP}"
    echo "Or for automatic setup: sudo certbot --nginx -d ${DOMAIN_OR_IP} --non-interactive --agree-tos --email your-email@example.com"
fi

echo "✅ Installation completed successfully!"
echo "🌐 Visit: http://${DOMAIN_OR_IP}/"
echo "🔧 Service status: sudo systemctl status attendance"
echo "📝 Logs: sudo journalctl -u attendance -f"
echo "🔄 Restart service: sudo systemctl restart attendance"

