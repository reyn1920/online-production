
# ONLINPRDUCTION – Anti-Loop Bundle (Add‑Only)

This package stops Trae.AI / agent infinite loops without editing existing code.
It installs a runtime guard and an auto-wrapper that activates on startup.

## What’s inside
- `bundle/backend/utils/loop_guard.py` – persistent guard (SQLite + memory)
- `bundle/backend/agents/middleware/guarded_runner.py` – step wrapper
- `bundle/sitecustomize.py` – auto-wrapper enabled at runtime (no code edits)
- `bundle/scripts/install.sh` – installer (clone repo, install files, set envs)
- `bundle/scripts/anti_loop_watchdog.sh` – loop health check
- `TraeAI_instructions.txt` – one-paste steps for Trae.AI

## Quick use
```bash
bash ONLINPRDUCTION_anti_loop_bundle_v1/bundle/scripts/install.sh
cd ~/ONLINPRDUCTION/repo
export APP_DIR="$HOME/ONLINPRDUCTION"
bash ./go_live_baremetal.sh
./scripts/anti_loop_watchdog.sh
```

**Notes**  
- Canonical project name: **ONLINPRDUCTION** (exact). Aliases created add-only.
- Repo remote name is unchanged to preserve links.
- Rule‑1 wording honored (prefer “runtime”); no deletions.
