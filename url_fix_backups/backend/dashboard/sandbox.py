import csv
import os
import time
from urllib.parse import urlencode

import requests
from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    send_from_directory,
)

sandbox_bp = Blueprint("sandbox", __name__, template_folder="templates", static_folder="static")

DASH_URL = os.environ.get("TRAE_DASH_URL", "http://127.0.0.1:8083")

ASSETS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets"))
ROADMAP_DIR = os.path.join(ASSETS_DIR, "incoming")
ROADMAP_PATH = os.path.join(ROADMAP_DIR, "channel_roadmaps_10.csv")


def ensure_assets_layout():
    """Create common asset directories if missing"""
    subdirs = [
        "",
        "incoming",
        "incoming / bundles",
        "incoming / roadmaps",
        "incoming / media",
        "releases",
        "releases / v1",
        "releases / v2",
        "releases / v3",
        "temp",
        "temp / synthesis",
        "temp / channels",
        "temp / processing",
        "generated",
        "avatars",
        "audio",
    ]
    for sd in subdirs:
        os.makedirs(os.path.join(ASSETS_DIR, sd), exist_ok=True)


def ensure_roadmap_seed():
    """Seed assets / incoming / channel_roadmaps_10.csv with demo channels if missing / empty"""
    ensure_assets_layout()
    if not os.path.exists(ROADMAP_PATH) or os.path.getsize(ROADMAP_PATH) == 0:
        rows = [
            ["channel"],
            ["DEMO_CAPABILITY_REEL"],
            ["TEST_CHANNEL"],
            ["QUICK_START"],
        ]
        with open(ROADMAP_PATH, "w", newline="") as f:
            csv.writer(f).writerows(rows)


@sandbox_bp.route("/sandbox", methods=["GET"])
def sandbox_page():
    """Creative Sandbox UI with auto - seeding"""
    try:
        ensure_roadmap_seed()
    except Exception as e:
        current_app.logger.warning("Sandbox seed warning: %s", e)
    return render_template("sandbox.html")


@sandbox_bp.route("/go / capability - reel", methods=["GET"])
def go_capability_reel():
    """Redirect route for home dashboard CTA button with autorun parameters"""
    q = {
        "autorun": "1",
        "minutes": request.args.get("minutes", "20"),
        "channel": request.args.get("channel", "DEMO_CAPABILITY_REEL"),
        "avatars": request.args.get("avatars", "Linly - Talker,TalkingHeads"),
        "fresh": request.args.get("fresh", "1"),
        "produce_examples": request.args.get("produce_examples", "1"),
    }
    return redirect(f"/sandbox?{urlencode(q)}", code=302)


@sandbox_bp.route("/api / sandbox / capability - reel", methods=["POST"])
def sandbox_capability_reel():
    """Proxy to existing Max - Out 'Run one channel' action with enhanced response handling"""
    payload = request.get_json(force=True, silent=True) or {}
    payload.setdefault("channel", "DEMO_CAPABILITY_REEL")
    payload.setdefault("minutes", 20)
    payload.setdefault("fresh", True)
    payload.setdefault("produce_examples", True)
    payload.setdefault("random_seed", int(time.time()))
    payload.setdefault("avatars", ["Linly - Talker", "TalkingHeads"])

    try:
        r = requests.post(
            f"{DASH_URL}/api / action / maxout / Run % 20one % 20channel",
            json=payload,
            timeout=300,
        )
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return jsonify({"ok": False, "error": str(e), "payload": payload}), 500

    body = data.get("result", data)

    def pick(d, *paths):
        """Extract nested values from response data"""
        for p in paths:
            cur = d
            for k in p.split("."):
                if isinstance(cur, dict) and k in cur:
                    cur = cur[k]
                else:
                    cur = None
                    break
            if cur:
                return cur
        return None

    def to_sandbox_url(path):
        """Convert filesystem paths to sandbox - accessible URLs"""
        if not path:
            return None
        path = str(path)
        if path.startswith("assets/"):
            return f"/sandbox / assets/{path[len('assets/'):]}"
        if os.path.isabs(path) and "assets" in path:
            tail = path.split("assets/", 1)[1]
            return f"/sandbox / assets/{tail}"
        return None

    resp = {
        "ok": bool(data.get("ok", True)),
        "payload": payload,
        "raw": data,
        "mp4_url": to_sandbox_url(pick(body, "mp4", "video", "artifacts.mp4", "outputs.mp4")),
        "pdf_url": to_sandbox_url(pick(body, "pdf", "ebook", "artifacts.pdf", "outputs.pdf")),
        "out_dir": to_sandbox_url(pick(body, "out_dir", "artifacts_dir", "outputs.dir")),
        "roadmap_csv": f"/sandbox / assets / incoming/{os.path.basename(ROADMAP_PATH)}",
    }
    return jsonify(resp), 200


@sandbox_bp.route("/sandbox / assets/<path:subpath>", methods=["GET"])
def sandbox_assets(subpath):
    """Serve files from assets directory for sandbox viewer"""
    return send_from_directory(ASSETS_DIR, subpath, conditional=True)
