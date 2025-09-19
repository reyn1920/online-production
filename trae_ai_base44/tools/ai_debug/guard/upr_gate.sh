#!/usr/bin/env bash
set -euo pipefail
LOG_DIR="logs/upr"
mkdir -p "$LOG_DIR"
echo "UPR run 1..."
make -C tools/ai_debug ci | tee "$LOG_DIR/run1.log"
echo "Rule-1 check..."
python3 tools/ai_debug/guard/rule1_guard.py | tee "$LOG_DIR/rule1_run1.log"
echo "UPR run 2..."
make -C tools/ai_debug ci | tee "$LOG_DIR/run2.log"
echo "Rule-1 check again..."
python3 tools/ai_debug/guard/rule1_guard.py | tee "$LOG_DIR/rule1_run2.log"
echo "UPR requirement satisfied if both runs succeeded."
