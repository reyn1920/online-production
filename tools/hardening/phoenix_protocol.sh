#!/usr/bin/env bash
set -euo pipefail

APP_MODULE="app.main:app"
PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"

bash tools/preflight_all.sh "."

backoff=1
while true; do
  python3 -m uvicorn "$APP_MODULE" --host "$HOST" --port "$PORT" || true
  sleep "$backoff"
  backoff=$(( backoff * 2 ))
  if [[ "$backoff" -gt 60 ]]; then backoff=60; fi
done
