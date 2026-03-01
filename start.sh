#!/bin/bash
# Fotosidan startup script - runs public and admin on separate ports

set -e

PYTHON=/root/.pyenv/versions/3.9.21/bin/python3

echo "Starting Fotosidan..."
echo "- Public gallery: http://0.0.0.0:8000 (NO admin routes)"
echo "- Admin portal: http://127.0.0.1:8001 (admin only, localhost)"

# Public gallery on port 8000 (NO admin routes)
nohup $PYTHON -m uvicorn fotosidan.main:app --host 0.0.0.0 --port 8000 > public.log 2>&1 &
PUBLIC_PID=$!
echo "✓ Public gallery started on port 8000 (PID: $PUBLIC_PID)"

# Admin on port 8001 (admin routes enabled, localhost only)
nohup env ENABLE_ADMIN=true $PYTHON -m uvicorn fotosidan.main:app --host 127.0.0.1 --port 8001 > admin.log 2>&1 &
ADMIN_PID=$!
echo "✓ Admin portal started on port 8001 (PID: $ADMIN_PID)"

echo ""
echo "Logs:"
echo "  - Public: public.log"
echo "  - Admin: admin.log"
