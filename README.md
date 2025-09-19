# TRAE.AI + Online Runtime Upgrade Pack (v3, Live/Bare‑Metal)
- Add-only merge into your existing app.
- **No virtual env** required; runs bare-metal via `python3 -m ...`.
- Preflight sweep runs twice before every start.
- Human-like web agent defaults to **headful** (visible) with real-time behavior.

## Quick Start (Mac)
```bash
export APP_DIR="$HOME/online production"
cd "$(dirname "$0")"
bash go_live_baremetal.sh
open "http://localhost:8000"
```
