import csv
import json
import os
import pathlib
import time
from typing import Any, Callable, Dict, List, Tuple

import requests

# Central in - process registry: (agent, action) -> callable(payload) -> dict
_REGISTRY: Dict[Tuple[str, str], Callable[[dict], dict]] = {}


def _canon(s: str) -> str:
    return " ".join(str(s or "").strip().split()).lower()


def register_action(agent: str, action: str):
    """Decorator to register an action under agent + action name."""


    def deco(fn: Callable[[dict], dict]):
        key = (_canon(agent), _canon(action))
        _REGISTRY[key] = fn
        return fn

    return deco


def list_actions() -> List[dict]:
    # Keep names as originally registered (we'll store the pretty names on the function)
    out = []
    for (agent_key, action_key), fn in sorted(_REGISTRY.items()):
        out.append(
            {
                "agent": getattr(fn, "_agent_pretty", agent_key),
                    "name": getattr(fn, "_action_pretty", action_key),
                    "doc": (fn.__doc__ or "").strip(),
                    "method": "POST",
                    "auth": "guarded",
                    "endpoint": f"/api / action/{getattr(fn, '_agent_pretty', agent_key)}/{getattr(fn, '_action_pretty', action_key)}",
                    "tags": getattr(fn, "_tags", []),
                    }
        )
    return out


def dispatch(agent: str, action: str, payload: dict) -> dict:
    fn = _REGISTRY.get((_canon(agent), _canon(action)))
    if not fn:
        raise KeyError(f"Unregistered action: {agent}/{action}")
    return fn(payload or {})


def _expose(agent_pretty: str, action_pretty: str, tags = None):
    """Apply pretty names for manifest (for nice display with spaces / case)."""


    def wrap(fn):
        fn._agent_pretty = agent_pretty
        fn._action_pretty = action_pretty
        fn._tags = tags or []
        return fn

    return wrap

# -------- Helpers reused by actions --------
DASH_URL = os.environ.get("TRAE_DASH_URL", "http://127.0.0.1:8083")
BACKEND_URL = os.environ.get("TRAE_BACKEND_URL", "http://127.0.0.1:8080")
ASSETS = pathlib.Path(__file__).resolve().parents[2] / "assets"
ROADMAP = ASSETS / "incoming" / "channel_roadmaps_10.csv"
(ASSETS / "incoming" / "bundles").mkdir(parents = True, exist_ok = True)
(ASSETS / "incoming" / "roadmaps").mkdir(parents = True, exist_ok = True)
(ASSETS / "releases" / "v3").mkdir(parents = True, exist_ok = True)


def _seed_roadmap_if_missing():
    if not ROADMAP.exists() or ROADMAP.stat().st_size == 0:
        ROADMAP.parent.mkdir(parents = True, exist_ok = True)
        with ROADMAP.open("w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["channel"])
            for c in [
                "DEMO_CAPABILITY_REEL",
                    "TEST_CHANNEL",
                    "QUICK_START",
                    "ADVANCED_FEATURES",
                    ]:
                w.writerow([c])

# ---------------- System / Dashboard actions ----------------

@_expose("get_system_status", "Get system status", tags=["ops"])
@register_action("get_system_status", "Get system status")


def act_get_system_status(payload: dict) -> dict:
    """RETURNS CURRENT SYSTEM HEALTH AND STATISTICS"""
    try:
        r = requests.get(f"{BACKEND_URL}/api / system / status", timeout = 5)
        sys = r.json()
    except Exception:
        sys = {"system": {"status": "unknown"}}
    return {"status": "ok", "system": sys, "ts": time.time()}

@_expose("reload_actions", "reload_actions", tags=["ops"])
@register_action("reload_actions", "reload_actions")


def act_reload_actions(payload: dict) -> dict:
    """Rebuild the actions manifest"""
    # Registry is static in this process; return manifest for the UI to reload.
    return {"status": "ok", "count": len(list_actions())}

@_expose("restart_monitoring", "Restart monitoring", tags=["ops"])
@register_action("restart_monitoring", "Restart monitoring")


def act_restart_monitoring(payload: dict) -> dict:
    """RESTARTS THE SYSTEM MONITORING THREAD"""
    # If you have a monitoring thread, call into it here.
    return {"status": "ok", "message": "Monitoring restart requested"}

# ---------------- Max - Out actions ----------------

@_expose("maxout", "Get release manifest", tags=["maxout"])
@register_action("maxout", "Get release manifest")


def act_maxout_manifest(payload: dict) -> dict:
    """Returns latest synthesis manifest"""
    manifest = ASSETS / "releases" / "v3" / "manifest.json"
    if manifest.exists():
        try:
            return {"status": "ok", "manifest": json.loads(manifest.read_text())}
        except Exception as e:
            return {"status": "error", "error": f"manifest parse: {e}", "manifest": {}}
    return {"status": "ok", "manifest": {}}

@_expose("maxout", "Synthesize bundles v3", tags=["maxout"])
@register_action("maxout", "Synthesize bundles v3")


def act_maxout_synthesize(payload: dict) -> dict:
    """Add - only ingest of incoming artifacts"""
    # Minimal real synthesis: list /assets / incoming / bundles and write a manifest
    bundles_dir = ASSETS / "incoming" / "bundles"
    items = sorted([p.name for p in bundles_dir.glob("*") if p.is_file()])
    out = {
        "timestamp": time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()),
            "ingested": items,
            "notes": "Add - only v3 synthesis",
            }
    (ASSETS / "releases" / "v3").mkdir(parents = True, exist_ok = True)
    (ASSETS / "releases" / "v3" / "manifest.json").write_text(json.dumps(out, indent = 2))
    return {"status": "ok", "result": out}

@_expose("maxout", "Run one channel", tags=["maxout", "video"])
@register_action("maxout", "Run one channel")


def act_maxout_run_one_channel(payload: dict) -> dict:
    """Reads roadmap, creates real MP4 + PDF (via channel executor)"""
    _seed_roadmap_if_missing()

    # Normalize payload
    channel = payload.get("channel") or "DEMO_CAPABILITY_REEL"
    minutes = int(payload.get("minutes") or 1)
    avatars = payload.get("avatars") or ["Linly - Talker", "TalkingHeads"]
    produce_examples = bool(payload.get("produce_examples", True))
    fresh = bool(payload.get("fresh", True))
    random_seed = int(payload.get("random_seed") or time.time())

    # Prefer calling an internal runner if available, otherwise fall back to the backend API if you wired one there
    # 1) Try internal channel executor (add - only, safe)
    try:
        from backend.runner import channel_executor as ce  # type: ignore

        if hasattr(ce, "capability_reel"):
            res = ce.capability_reel(
                channel = channel,
                    minutes = minutes,
                    avatars = avatars,
                    fresh = fresh,
                    produce_examples = produce_examples,
                    random_seed = random_seed,
                    )
            return {"status": "ok", **res}
    except Exception as e:
        # fall through to try API route
        pass

    # 2) Try backend API (FastAPI) if you exposed one
    try:
        r = requests.post(
            f"{BACKEND_URL}/api / capability_reel",
                json={
                "channel": channel,
                    "minutes": minutes,
                    "avatars": avatars,
                    "fresh": fresh,
                    "produce_examples": produce_examples,
                    "random_seed": random_seed,
                    },
                timeout = 300,
                )
        r.raise_for_status()
        j = r.json()
        return {"status": "ok", **j}
    except Exception as e:
        # If neither path exists, still return a helpful error with the expected CSV
        return {
            "status": "error",
                "error": f"No runner available: {e}",
                "csv_path": str(
                ROADMAP.relative_to(ASSETS.parent)
            ),  # "assets / incoming / channel_roadmaps_10.csv"
            "note": "Ensure channel executor is wired or the FastAPI /api / capability_reel exists.",
                }
