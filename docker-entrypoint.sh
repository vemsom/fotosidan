#!/bin/bash
set -e

# Start public gallery on 0.0.0.0:8000 (exposed)
echo "Starting public gallery on port 8000..."
uvicorn fotosidan.main:app --host 0.0.0.0 --port 8000 &
PUBLIC_PID=$!

# Start admin portal on 127.0.0.1:8001 (local only, NOT exposed)
echo "Starting admin portal on port 8001 (local only)..."
uvicorn fotosidan.main:app --host 127.0.0.1 --port 8001 &
ADMIN_PID=$!

# Wait for both processes
wait $PUBLIC_PID $ADMIN_PID
