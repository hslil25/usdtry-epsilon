#!/bin/bash
# start.sh — launch backend + frontend in parallel

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== USD/TRY ε Dashboard ==="

# Check .env exists
if [ ! -f "$SCRIPT_DIR/.env" ]; then
  echo "No .env found — copying .env.example"
  cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
  echo "Edit .env and set FRED_API_KEY and R_TRY before running."
fi

# Install Python deps if needed
echo "Checking Python dependencies..."
cd "$SCRIPT_DIR"
pip3 install -r backend/requirements.txt -q

# Install frontend deps if needed
echo "Checking frontend dependencies..."
cd "$SCRIPT_DIR/frontend"
if [ ! -d node_modules ]; then
  npm install
fi

# Start backend
echo ""
echo "Starting FastAPI backend on http://localhost:8000 ..."
cd "$SCRIPT_DIR"
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

sleep 2

# Start frontend
echo "Starting React frontend on http://localhost:5173 ..."
cd "$SCRIPT_DIR/frontend"
./node_modules/.bin/vite &
FRONTEND_PID=$!

echo ""
echo "Dashboard → http://localhost:5173"
echo "API       → http://localhost:8000/snapshot"
echo ""
echo "Press Ctrl+C to stop both servers."

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
