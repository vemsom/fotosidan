#!/bin/bash
# Fotosidan startup script - runs public and admin on separate ports

set -e

echo "Starting Fotosidan..."
echo "- Public gallery: http://0.0.0.0:8000"
echo "- Admin portal: http://127.0.0.1:8001 (local only)"

# Public gallery on port 8000 (accessible from anywhere)
uvicorn fotosidan.main:app --host 0.0.0.0 --port 8000 --loop asyncio &
PUBLIC_PID=$!
echo "Public gallery started (PID: $PUBLIC_PID)"

# Admin on port 8001 (localhost only, not accessible externally)
uvicorn fotosidan.main:app --host 127.0.0.1 --port 8001 --loop asyncio &
ADMIN_PID=$!
echo "Admin portal started on localhost (PID: $ADMIN_PID)"

echo "Both servers running. Press Ctrl+C to stop."

# Wait for both processes
wait $PUBLIC_PID $ADMIN_PID
