#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
if [ ! -d .venv ]; then
  python3 -m venv .venv
  source .venv/bin/activate
  python -m pip install -q --upgrade pip
  pip install -q -r requirements.txt
else
  source .venv/bin/activate
fi
if [ ! -f .env ]; then cp .env.example .env; fi
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000