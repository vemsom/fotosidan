#!/bin/bash
# Install Fotosidan as systemd services

set -e

PYTHON=/root/.pyenv/versions/3.9.21/bin/python3
WORKDIR=/srv/fotosidan

echo "Installing Fotosidan systemd services..."

# Kill any running instances
pkill -f "uvicorn fotosidan" 2>/dev/null || true

# Stop existing services
sudo systemctl stop fotosidan-public fotosidan-admin 2>/dev/null || true

# Create public service (NO admin routes)
sudo tee /etc/systemd/system/fotosidan-public.service > /dev/null <<'EOF'
[Unit]
Description=Fotosidan Public Gallery
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/srv/fotosidan
ExecStart=/root/.pyenv/versions/3.9.21/bin/python3 -m uvicorn fotosidan.app_public:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Create admin service (WITH admin routes, localhost only)
sudo tee /etc/systemd/system/fotosidan-admin.service > /dev/null <<'EOF'
[Unit]
Description=Fotosidan Admin Portal
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/srv/fotosidan
ExecStart=/root/.pyenv/versions/3.9.21/bin/python3 -m uvicorn fotosidan.app_admin:app --host 127.0.0.1 --port 8001
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Reload and enable
sudo systemctl daemon-reload
sudo systemctl enable fotosidan-public fotosidan-admin
sudo systemctl start fotosidan-public fotosidan-admin

echo "✓ Services installed and started"
echo ""
echo "Status:"
sudo systemctl status fotosidan-public fotosidan-admin

echo ""
echo "Access:"
echo "  Public: http://localhost:8000"
echo "  Admin: http://localhost:8001/admin/photos (localhost only)"
