#!/usr/bin/env bash
set -euo pipefail

OUT=tools/puppeteer/output
mkdir -p "$OUT"

echo "Running device matrix..."
node tools/puppeteer/device_matrix.js --output "$OUT" || true

echo "Running screenshot checks..."
node tools/puppeteer/screenshot_check.js --output "$OUT" || true

echo "Collecting trace..."
node tools/puppeteer/trace_run.js --output "$OUT/trace.json" || true

echo "Puppeteer full suite complete; artifacts: $OUT"
