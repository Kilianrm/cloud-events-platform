#!/bin/bash
# Starts the live demo UI on http://localhost:8000 (run from Linux / WSL).
set -e

DEMO_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV="$DEMO_DIR/.venv"
PORT="${PORT:-8000}"
# 0.0.0.0 so WSL forwards the port to Windows' localhost (127.0.0.1 is not always forwarded).
HOST="${HOST:-0.0.0.0}"

for tool in terraform python3; do
    command -v "$tool" >/dev/null || { echo "❌ $tool is required"; exit 1; }
done

if [ ! -x "$VENV/bin/python" ]; then
    echo "🐍 Creating virtual environment in demo/.venv..."
    PY=$(command -v python3.11 || command -v python3)
    "$PY" -m venv "$VENV"
fi

# Reinstall dependencies only when requirements.txt changes
STAMP="$VENV/.requirements.sha"
SHA=$(sha256sum "$DEMO_DIR/requirements.txt" | cut -d' ' -f1)
if [ "$(cat "$STAMP" 2>/dev/null)" != "$SHA" ]; then
    echo "📦 Installing demo dependencies..."
    "$VENV/bin/pip" install -q --upgrade pip
    "$VENV/bin/pip" install -q -r "$DEMO_DIR/requirements.txt"
    echo "$SHA" > "$STAMP"
fi

echo "🚀 Demo UI on http://localhost:$PORT"
exec "$VENV/bin/python" -m uvicorn server:app --app-dir "$DEMO_DIR" --host "$HOST" --port "$PORT"
