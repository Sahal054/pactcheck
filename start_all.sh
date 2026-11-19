#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"

cleanup() {
  echo "Stopping backend and frontend..."
  pkill -f "uvicorn app.main:app" 2>/dev/null || true
  pkill -f "vite" 2>/dev/null || true
  kill $(jobs -p) 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(cd "$ROOT/backend" && bash start_backend.sh) &
(cd "$ROOT/frontend" && bash start_frontend.sh) &
wait