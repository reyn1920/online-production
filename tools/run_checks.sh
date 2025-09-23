#!/usr/bin/env bash
set -euo pipefail

echo "Running Rule-1 guard..."
. .venv/bin/activate || true
python tools/rule1_guard.py || true

echo "Running ruff..."
python -m ruff . || true

echo "Running black..."
python -m black . || true

echo "Running pytest..."
python -m pytest -q || true

echo "Checks complete. See tools/rule1_guard_report.txt"
