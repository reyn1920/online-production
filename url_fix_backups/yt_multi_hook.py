#!/usr / bin / env python3
"""
Multi - channel YouTube → Live Dashboard updater (safe by default).
- Stdlib only (urllib), works with Python 3.13+
- Defaults to DRY RUN (prints payload). Add --post to push to dashboard.
- Supports: primary channel or all channels (aggregate)
- Revenue: set explicitly with --revenue, or leave 0.0 (no guesswork)
Usage examples:
  export YT_API_KEY = YOUR_KEY
  python3 yt_multi_hook.py --channel primary
  python3 yt_multi_hook.py --channel primary --post
  python3 yt_multi_hook.py --all --post
  python3 yt_multi_hook.py --channel NextGenTechToday --revenue 25.00 --post
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from typing import Any, Dict, List

# ---- Your channels (from your message) --------------------------------------
CHANNELS: Dict[str, Dict[str, Any]] = {
    "primary": {
        "label": "The Right Perspective",
        "handle": "@therightperspective7777",
        "id": "UC_fz1kiUOIDz5 - VtVtKn7OQ",
        "slot": "6 PM EST",
        "target_len": "12 - 15 min",
        "voice": "Matthew (Speechelo)",
        "email": "test@example.com",
        "monetization": ["High - value ads", "Merch", "Affiliate"],
    },
    "NextGenTechToday": {
        "label": "Next Gen Tech Today",
        "handle": "@NextGenTechToday",
        "id": "UC8pIkBnof0r5Fh6h5nxPh7g",
        "slot": "8 PM EST",
        "target_len": "10 - 12 min",
        "voice": "David (Speechelo)",
        "email": "test@example.com",
        "monetization": ["Tech affiliate", "Sponsored reviews"],
    },
    "EcoWellLiving": {
        "label": "EcoWell Living",
        "handle": "@EcoWellLiving",
        "id": "UC_p_3vPbe6gpM8VK2uF2B6Q",
        "slot": "4 PM EST",
        "target_len": "12 - 15 min",
        "voice": "Brian (Speechelo)",
        "email": "test@example.com",
        "monetization": ["Eco partners", "Wellness services"],
    },
    "AITrendReports": {
        "label": "AI Trend Reports",
        "handle": "@AITrendReports",
        "id": "UC4wNMA9Xi0aJ_9kvJy6KBTQ",
        "slot": "7 PM EST",
        "target_len": "15 - 18 min",
        "voice": "Alex (Speechelo)",
        "email": "test@example.com",
        "monetization": ["AI tool affiliates", "Courses"],
    },
}

# ---- Config via env (override as needed) ------------------------------------
API_KEY = os.environ.get("YT_API_KEY", "").strip()
DASHBOARD = os.environ.get("DASH_URL", "http://localhost:8000 / api / update - metrics").strip()


def yt(endpoint: str, params: Dict[str, str]) -> Dict[str, Any]:
    url = f"https://www.googleapis.com / youtube / v3/{endpoint}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url) as r:
        return json.loads(r.read().decode())


def get_channel_stats(api_key: str, channel_id: str) -> Dict[str, int]:
    data = yt("channels", {"part": "statistics", "id": channel_id, "key": api_key})
    items = data.get("items", [])
    if not items:
        raise RuntimeError(f"No channel found for id={channel_id}")
    s = items[0]["statistics"]
    return {
        "views": int(s.get("viewCount", 0)),
        "subscribers": int(s.get("subscriberCount", 0)),
        "active_videos": int(s.get("videoCount", 0)),
    }


def compose_payload(stats: Dict[str, int], revenue: float = 0.0) -> Dict[str, Any]:
    # Matches your FastAPI dashboard expected keys exactly
    return {
        "views": stats["views"],
        "revenue": float(revenue),
        "subscribers": stats["subscribers"],
        "engagement": 0,  # You can wire a real calc later
        "active_videos": stats["active_videos"],
        "trending_topics": [],  # Placeholder until you feed topics
    }


def post_dashboard(url: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, headers={"Content - Type": "application / json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read().decode())


def aggregate_stats(items: List[Dict[str, int]]) -> Dict[str, int]:
    out = {"views": 0, "subscribers": 0, "active_videos": 0}
    for s in items:
        out["views"] += s.get("views", 0)
        out["subscribers"] += s.get("subscribers", 0)
        out["active_videos"] += s.get("active_videos", 0)
    return out


def resolve_channel(arg: str) -> Dict[str, Any]:
    # Accept key ("primary") or label / handle / id match
    if arg in CHANNELS:
        return CHANNELS[arg]
    # try handle, label, or raw id match
    for meta in CHANNELS.values():
        if arg == meta["handle"] or arg == meta["label"] or arg == meta["id"]:
            return meta
    raise SystemExit(f"Unknown channel '{arg}'. Use one of: {', '.join(CHANNELS.keys())}")


def main():
    p = argparse.ArgumentParser(description="Update live dashboard from YouTube stats")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument(
        "--channel",
        help="Channel key / handle / label / id (e.g. primary, @NextGenTechToday)",
    )
    g.add_argument("--all", action="store_true", help="Aggregate all channels")
    p.add_argument("--revenue", type=float, default=0.0, help="Revenue to display (default 0.0)")
    p.add_argument("--post", action="store_true", help="POST to dashboard (otherwise print only)")
    p.add_argument(
        "--dashboard",
        default=DASHBOARD,
        help=f"Dashboard endpoint (default {DASHBOARD})",
    )
    args = p.parse_args()

    if not API_KEY:
        print("YT_API_KEY is not set. Dry - run only (no API calls).", file=sys.stderr)

    try:
        if args.all:
            # Aggregate across all channels
            stats_list = []
            for key, meta in CHANNELS.items():
                if not API_KEY:
                    # Dry - run fake values if no API key
                    stats_list.append({"views": 0, "subscribers": 0, "active_videos": 0})
                else:
                    stats_list.append(get_channel_stats(API_KEY, meta["id"]))
            agg = aggregate_stats(stats_list)
            payload = compose_payload(agg, revenue=args.revenue)
            print("[ALL] Payload:", json.dumps(payload, indent=2))
            if args.post:
                res = post_dashboard(args.dashboard, payload)
                print("[ALL] Dashboard response:", json.dumps(res, indent=2))
            return

        # Single channel
        meta = resolve_channel(args.channel)
        if API_KEY:
            stats = get_channel_stats(API_KEY, meta["id"])
        else:
            stats = {"views": 0, "subscribers": 0, "active_videos": 0}  # Dry - run
        payload = compose_payload(stats, revenue=args.revenue)
        print(f"[{meta['label']}] Payload:", json.dumps(payload, indent=2))
        if args.post:
            res = post_dashboard(args.dashboard, payload)
            print(f"[{meta['label']}] Dashboard response:", json.dumps(res, indent=2))

    except urllib.error.HTTPError as e:
        msg = e.read().decode() if hasattr(e, "read") else str(e)
        print(f"HTTPError: {e.code} {e.reason}\\n{msg}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
