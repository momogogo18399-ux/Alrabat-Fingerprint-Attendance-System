#!/usr/bin/env bash
set -euo pipefail

# Usage (Ubuntu):
#   curl -fsSL https://raw.githubusercontent.com/YOUR_USER/YOUR_REPO/main/deploy/install_vps.sh | bash -s -- \
#     --repo-url https://github.com/YOUR_USER/YOUR_REPO.git \
#     --domain YOUR_DOMAIN_OR_IP \
#     --db-url "postgresql://attendance:strongpass@127.0.0.1:5432/attendance"

REPO_URL=""
DOMAIN_OR_IP=""
DB_URL=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --repo-url) REPO_URL="$2"; shift 2 ;;
    --domain) DOMAIN_OR_IP="$2"; shift 2 ;;
    --db-url) DB_URL="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

if [[ -z "$REPO_URL" || -z "$DOMAIN_OR_IP" ]]; then
  echo "Missing required args. Example: --repo-url https://github.com/you/repo.git --domain your.ip" >&2
  exit 1
fi

echo "[1/6] Installing packages..."
sudo apt update
sudo apt install -y python3-pip python3-venv nginx git

echo "[2/6] Creating service user and directory..."
sudo adduser --system --group attendance || true
sudo mkdir -p /opt/attendance
sudo chown -R attendance:attendance /opt/attendance

echo "[3/6] Cloning repo and creating venv..."
sudo -u attendance bash -lc "cd /opt/attendance && git clone '$REPO_URL' ."
sudo -u attendance bash -lc "cd /opt/attendance && python3 -m venv .venv && source .venv/bin/activate && pip install --upgrade pip setuptools wheel && pip install -r requirements.txt"

echo "[4/6] Writing .env..."
sudo -u attendance bash -lc "cat > /opt/attendance/.env <<ENV
FLASK_DEBUG=0
SQLITE_FILE=/opt/attendance/attendance.db
THEME_DIR=/opt/attendance/assets/themes
NOTIFIER_HOST=localhost
NOTIFIER_PORT=8989
${DB_URL:+DATABASE_URL=$DB_URL}
ENV"

echo "[5/6] Creating systemd service..."
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
ExecStart=/opt/attendance/.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 web_app:app
Restart=always

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now attendance

echo "[6/6] Configuring Nginx..."
sudo tee /etc/nginx/sites-available/attendance >/dev/null <<NGINX
server {
    listen 80;
    server_name ${DOMAIN_OR_IP};

    client_max_body_size 10m;

    location /healthz {
        proxy_pass http://127.0.0.1:8000/healthz;
    }

    location / {
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_pass http://127.0.0.1:8000;
    }
}
NGINX

sudo ln -sf /etc/nginx/sites-available/attendance /etc/nginx/sites-enabled/attendance
sudo nginx -t
sudo systemctl reload nginx

echo "Done. Visit: http://${DOMAIN_OR_IP}/"

