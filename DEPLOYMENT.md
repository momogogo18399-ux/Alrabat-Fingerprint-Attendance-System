## VPS Deployment Guide (Ubuntu)

This guide deploys the Flask web app with Gunicorn behind Nginx using SQLite. The desktop app (PyQt6) is optional and requires a GUI environment, so it’s not covered here.

Important note about the database:

- The current code uses a local SQLite file `attendance.db`. Web and desktop apps must run on the same machine to share this file. If you need remote access from your PC desktop app while the web app runs on the server, migrate to PostgreSQL (future change).

### 1) Install OS packages

```bash
sudo apt update && sudo apt install -y python3-pip python3-venv nginx
sudo adduser --system --group attendance
sudo mkdir -p /opt/attendance && sudo chown -R attendance:attendance /opt/attendance
```

### 2) Clone and install Python dependencies

```bash
sudo -u attendance bash -lc '
cd /opt/attendance
git clone YOUR_REPO_URL .
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
'
```

Create an .env file (optional, recommended):

```bash
sudo -u attendance bash -lc 'cat > /opt/attendance/.env <<EOF
# Example PostgreSQL URL
# DATABASE_URL=postgresql://attendance:strongpass@127.0.0.1:5432/attendance
FLASK_DEBUG=0
EOF'
```

Ensure `attendance.db` will be created/owned by the service user:

```bash
sudo -u attendance bash -lc 'cd /opt/attendance && touch attendance.db'
sudo chown attendance:attendance /opt/attendance/attendance.db
```

Note: The app also auto-initializes the DB on first run.

### 3) Create systemd service (Gunicorn)

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
ExecStart=/opt/attendance/.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 web_app:app
Restart=always
EnvironmentFile=/opt/attendance/.env

[Install]
WantedBy=multi-user.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now attendance
sudo systemctl status attendance --no-pager
```

### 4) Configure Nginx reverse proxy

```bash
sudo tee /etc/nginx/sites-available/attendance >/dev/null <<'NGINX'
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_SERVER_IP;

    client_max_body_size 10m;

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
sudo nginx -t && sudo systemctl reload nginx
```

Optional: Enable HTTPS with Let’s Encrypt

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d YOUR_DOMAIN
```

### 5) Smoke test

- Open http://YOUR_DOMAIN_OR_SERVER_IP/
- Perform a check-in from a phone; the server should write to `attendance.db`.

### 6) Maintenance

Update and restart:

```bash
sudo -u attendance bash -lc 'cd /opt/attendance && git pull && source .venv/bin/activate && pip install -r requirements.txt'
sudo systemctl restart attendance
```

### Environment variables (.env)

Place at `/opt/attendance/.env` and the app will auto-load:

```
# Switch to PostgreSQL. If unset, SQLite is used.
# DATABASE_URL=postgresql://attendance:strongpass@127.0.0.1:5432/attendance

# SQLite file (only when DATABASE_URL is not set)
SQLITE_FILE=/opt/attendance/attendance.db

# Flask debug for local runs
FLASK_DEBUG=0

# Desktop notifier host/port (for desktop app usage on the same machine)
NOTIFIER_HOST=localhost
NOTIFIER_PORT=8989

# Directory for QSS themes used by the desktop app
THEME_DIR=/opt/attendance/assets/themes
```



