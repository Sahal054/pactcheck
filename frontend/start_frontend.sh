#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

node_major="$(node -p 'process.versions.node.split(".")[0]')"
if [ "$node_major" -lt 20 ]; then
  echo "Node.js 20+ is required (found $(node --version)). Upgrade Node.js and retry."
  exit 1
fi

if [ ! -d node_modules ]; then
  npm install --silent
fi
npm run dev