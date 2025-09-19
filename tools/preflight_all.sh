#!/usr/bin/env bash
set -euo pipefail
ROOT="${1:-.}"
python3 tools/debug_sweep.py --root "$ROOT" --full --fix
python3 tools/debug_sweep.py --root "$ROOT" --full --fix
echo "[preflight] clean x2"
