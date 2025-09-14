"""
Add - only actions that make the dashboard 'Total Access':
- synthesize_bundles_v3
- run_one_channel (reads the roadmap, produces MP4 + PDF)
- get_release_manifest (optional: peek the latest synthesis manifest)
"""

import json
import traceback
from pathlib import Path
from typing import Any, Dict

from app.actions import dashboard_action


@dashboard_action(name="Synthesize bundles v3", doc="Add - only ingest of incoming artifacts")
def synthesize_bundles_v3(payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    try:
        import sys

        from scripts.synthesize_release_v3 import main as synth

        base_dir = (payload or {}).get("base_dir", "assets")
        sys.argv = ["synthesize_release_v3.py", "--base - dir", base_dir]
        rc = synth()
        latest = Path(base_dir) / "releases"
        manifest = {}
        if latest.exists():
            dirs = sorted([d for d in latest.iterdir() if d.is_dir()])
            if dirs and (dirs[-1] / "synthesis_manifest.json").exists():
                manifest = json.loads((dirs[-1] / "synthesis_manifest.json").read_text())
        return {"status": "ok", "code": rc, "manifest": manifest}
    except Exception as e:
        return {"status": "error", "error": str(e), "trace": traceback.format_exc()}


@dashboard_action(name="Run one channel", doc="Reads roadmap, creates real MP4 & PDF")
def run_one_channel(payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    try:
        from backend.runner.channel_executor import run_channel_once

        csv_path = (payload or {}).get("csv", "assets/incoming/channel_roadmaps_10.csv")
        out_v = (payload or {}).get("video_dir", "outputs/videos")
        out_p = (payload or {}).get("pdf_dir", "outputs/lead_magnets")
        res = run_channel_once(csv_path, out_v, out_p)
        return res
    except Exception as e:
        return {"status": "error", "error": str(e), "trace": traceback.format_exc()}


@dashboard_action(
    name="Get release manifest", doc="Returns latest synthesis manifest", method="POST"
)
def get_release_manifest(payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    try:
        out = (payload or {}).get("out", "assets")
        latest = Path(out) / "releases"
        if not latest.exists():
            return {"status": "ok", "manifest": {}}
        dirs = sorted([d for d in latest.iterdir() if d.is_dir()])
        if not dirs:
            return {"status": "ok", "manifest": {}}
        man = dirs[-1] / "synthesis_manifest.json"
        if man.exists():
            import json

            return {"status": "ok", "manifest": json.loads(man.read_text())}
        return {"status": "ok", "manifest": {}}
    except Exception as e:
        return {"status": "error", "error": str(e)}
