# TRAE.AI Base44 — Dual Runtime System

A runtime-ready dual system with automated guards, monitoring, and deployment pipelines.

## Quick Start

### Local Setup

```bash
# 1) Navigate to the project
cd trae_ai_base44

# 2) Local env config
cp configs/env.local.example .env

# 3) Initialize Python environment
make init

# 4) Run guard suite and start API
make check && make run
```

### Verification

```bash
# Open dashboard
open frontend/index.html

# Test API endpoints
curl -s http://127.0.0.1:7860/ | python3 -c "import sys,json; print(json.load(sys.stdin))"
curl -s http://127.0.0.1:7860/health | python3 -c "import sys,json; d=json.load(sys.stdin); print('OK' if d.get('ok') else 'FAIL', d)"
```

## System Components

### Guard Scripts
- **Rule-1 Guard**: Vocabulary enforcement (`scripts/rule1_guard.py`)
- **Python Audit**: Syntax validation (`scripts/py_audit.py`)
- **UPR Monitor**: Two consecutive clean passes required (`scripts/upr_monitor.py`)

### Monitoring
- **Watchdog**: System health checks every 5 minutes (`scripts/watchdog.sh`)
- **Phoenix Protocol**: Automated backup system (`scripts/phoenix_protocol.sh`)

### Deployment
- **GitHub Actions**: Automated CI/CD pipeline (`.github/workflows/ci.yml`)
- **Netlify**: Frontend hosting with serverless functions (`netlify.toml`)

## Installation Commands

### Watchdog Setup
```bash
# Install system watchdog (runs every 5 minutes)
sed -i '' "s#__REPO_ROOT__#$(pwd)#" launchd/com.traeai.watchdog.plist
cp launchd/com.traeai.watchdog.plist ~/Library/LaunchAgents/
launchctl unload ~/Library/LaunchAgents/com.traeai.watchdog.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/com.traeai.watchdog.plist
```

### Phoenix Backup
```bash
# Create safe system snapshot
bash scripts/phoenix_protocol.sh
```

### GitHub Pages Deployment
```bash
# Initialize git repository
git init
git add -A
git commit -m "init: Base44 dual runtime with guards and CI"
git branch -M main
git remote add origin <YOUR_GITHUB_REPO_URL>
git push -u origin main
```

**GitHub Setup:**
1. Go to Settings → Pages → Build and deployment: Source = "GitHub Actions"
2. Run "CI/CD Pipeline" workflow in Actions tab
3. Access your site at `https://<username>.github.io/<repo>/`

## Verification Checklist

### Local Runtime ✅
- [ ] Dashboard shows: API: online (ok)
- [ ] `curl 127.0.0.1:7860/health` returns `{"ok": true, "status": "ok"}`
- [ ] `python3 scripts/upr_monitor.py` shows two consecutive clean passes

### Online Runtime ✅
- [ ] GitHub Actions workflow completes successfully:
  - [ ] "Run Rule-1 Guard" ✅
  - [ ] "Run Python Audit" ✅ 
  - [ ] "Run UPR Monitor" ✅
- [ ] GitHub Pages URL serves frontend/index.html
- [ ] (Optional) Netlify function returns `{"ok": true, "timestamp": ...}`

## Rollback Procedures

- **Phoenix Backup**: Use the backup path printed by `scripts/phoenix_protocol.sh`
- **Git Rollback**: `git log` → `git revert <commit>` or `git checkout <commit> -- <path>`

## Architecture

```
trae_ai_base44/
├── configs/           # Environment configurations
├── scripts/           # Guard and monitoring scripts
├── backend/           # FastAPI application
├── frontend/          # Status dashboard
├── launchd/           # macOS system integration
├── netlify/           # Serverless functions
├── .github/           # CI/CD workflows
└── logs/              # System logs
```

## Governance

- **Rule-1**: Vocabulary enforcement (see `GOVERNANCE.md`)
- **UPR**: Universal Persistence Rule - no destructive operations
- **No-Delete Policy**: Protected assets listed in `DO_NOT_DELETE.md`

For detailed governance rules, see `GOVERNANCE.md` and `DO_NOT_DELETE.md`.