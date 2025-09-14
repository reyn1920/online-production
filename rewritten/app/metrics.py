# ADD - ONLY: Metrics aggregator +/api/metrics route
# Safe on systems without psutil; falls back to stdlib.

from __future__ import annotations

import glob
import os
import shutil
import time
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from flask import Blueprint, current_app, jsonify

try:
    import psutil  # optional

except Exception:  # pragma: no cover
    psutil = None

metrics_bp = Blueprint("metrics_bp", __name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        current_app.logger.debug("metrics error:\\n % s", traceback.format_exc())
        return default


def _system_stats() -> Dict[str, Any]:
    # CPU/MEM/DISK (best - effort)
    cpu = _safe(lambda: psutil.cpu_percent(interval=0.1) if psutil else None)
    vm = _safe(lambda: psutil.virtual_memory()._asdict() if psutil else None)
    du = _safe(lambda: shutil.disk_usage(os.getcwd()))
    return {
        "cpu_percent": cpu,
        "memory": (
            {
                "total": vm["total"],
                "used": vm["used"],
                "available": vm["available"],
                "percent": vm["percent"],
            }
            if isinstance(vm, dict)
            else None
        ),
        "disk": ({"total": du.total, "used": du.used, "free": du.free} if du else None),
    }


def _db_inventory() -> Dict[str, Any]:
    # Discover *.db under common locations; size + mtime
    roots = list({os.getenv("TRAE_DB_DIR", "data"), "data", "backend/database", "db", "."})
    found: List[Dict[str, Any]] = []
    for root in roots:
        for path in glob.glob(os.path.join(root, "**", "*.db"), recursive=True):
            try:
                st = os.stat(path)
                found.append(
                    {
                        "path": os.path.relpath(path),
                        "size_bytes": st.st_size,
                        "modified": datetime.fromtimestamp(
                            st.st_mtime, tz=timezone.utc
                        ).isoformat(),
                    }
                )
            except FileNotFoundError:
                continue
            except Exception:
                current_app.logger.debug("db stat error %s\\n % s", path, traceback.format_exc())
    return {
        "count": len(found),
        # cap to keep payload light
        "databases": sorted(found, key=lambda x: x["path"])[:20],
    }


def _latest_backup() -> Optional[Dict[str, Any]]:
    backup_dir = os.getenv("TRAE_BACKUP_DIR", "backups")
    patterns = ["*.bak", "*.sqlite", "*.db", "*.zip"]
    paths: List[str] = []
    for pat in patterns:
        paths.extend(glob.glob(os.path.join(backup_dir, "**", pat), recursive=True))
    best = None
    for p in paths:
        try:
            st = os.stat(p)
            if not best or st.st_mtime > best["st_mtime"]:
                best = {
                    "path": os.path.relpath(p),
                    "st_mtime": st.st_mtime,
                    "size_bytes": st.st_size,
                }
        except Exception:
            continue
    if not best:
        return None
    best["timestamp"] = datetime.fromtimestamp(best["st_mtime"], tz=timezone.utc).isoformat()
    best["age_seconds"] = max(0, time.time() - best["st_mtime"])
    del best["st_mtime"]
    return best


def _version_info() -> Dict[str, Any]:
    # Reuse/api/version if available (non - blocking)
    try:
        # If you have a version provider on app config, use it
        provider = current_app.config.get("VERSION_PROVIDER")
        if callable(provider):
            return provider()
    except Exception:
        pass
    # Fallback to env
    return {
        "service": os.getenv("TRAE_SERVICE", "TRAE.AI Dashboard"),
        "commit": os.getenv("TRAE_COMMIT", "unknown"),
        "build_time": os.getenv("TRAE_BUILD_TIME", "unknown"),
        "pid": os.getpid(),
    }


def _agent_snapshot() -> Dict[str, Any]:
    """
    Best - effort: if orchestrator exports a snapshot provider, use it.
    Else return None fields; UI can handle absence gracefully.
    """
    snap = None
    provider = current_app.config.get("AGENT_SNAPSHOT_PROVIDER")
    if callable(provider):
        snap = _safe(provider, default=None)
    if not snap:
        return {"total": None, "active": None, "agents": None}
    # Normalize minimal shape
    total = _safe(lambda: len(snap.get("agents", [])))
    active = _safe(
        lambda: sum(1 for a in snap.get("agents", []) if a.get("status") in {"busy", "processing"})
    )
    return {"total": total, "active": active, "agents": snap.get("agents")}


@metrics_bp.route("/api/metrics", methods=["GET"])
def metrics_route():
    payload = {
        "timestamp": _now_iso(),
        "version": _version_info(),
        "system": _system_stats(),
        "database": _db_inventory(),
        "latest_backup": _latest_backup(),
        "agents": _agent_snapshot(),
        # Optional: very light error count by tailing run.log (best - effort)
        "errors": _safe(lambda: _tail_error_count(), default=None),
    }
    return jsonify(payload), 200


def _tail_error_count(lines: int = 2000) -> Dict[str, Any]:
    path = os.getenv("TRAE_RUNLOG_PATH", "run.log")
    if not os.path.exists(path):
        return {"file": path, "present": False}
    cnt = 0
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            f.seek(max(0, size - 200_000))
            for raw in f.readlines()[-lines:]:
                try:
                    line = raw.decode("utf - 8", "ignore")
                except Exception:
                    continue
                if " ERROR " in line or line.startswith("ERROR"):
                    cnt += 1
    except Exception:
        current_app.logger.debug("tail error\\n % s", traceback.format_exc())
    return {"file": path, "present": True, "errors_last_chunk": cnt}


def register_metrics_routes(app):
    # ADD - ONLY hook
    app.register_blueprint(metrics_bp)
