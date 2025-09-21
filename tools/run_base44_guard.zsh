#!/usr/bin/env zsh
set -euo pipefail
SCRIPT_DIR="${0:A:h}"
ROOT="${SCRIPT_DIR:h}"
echo "[Base44Guard] starting..."
python3 "$SCRIPT_DIR/base44_debug_guard.py"
echo "[Base44Guard] finished."
