#!/usr/bin/env bash
set -e
ROOT="$(cd "$(dirname "$0")" && pwd)"
(cd "$ROOT/backend" && bash start_backend.sh) &
(cd "$ROOT/frontend" && bash start_frontend.sh) &
wait
