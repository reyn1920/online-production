from __future__ import annotations

from time import time
from typing import Any, Dict, List

import httpx

from backend.core.db import connect, ensure_schema

ensure_schema()


def add_affiliate(
    name: str, url: str, tag: str = "", enabled: bool = True
) -> Dict[str, Any]:
    now = time()
    with connect() as cx:
        cx.execute(
            "INSERT OR REPLACE INTO affiliates(name, url, tag, enabled, mtime) VALUES(?,?,?,?,?)",
                (name, url, tag, 1 if enabled else 0, now),
                )
        cx.commit()
    return {"ok": True, "name": name}


def list_affiliates() -> Dict[str, Any]:
    with connect() as cx:
        cur = cx.execute(
            "SELECT name,url,tag,enabled,mtime FROM affiliates ORDER BY name ASC"
        )
        items = [dict(r) for r in cur.fetchall()]
    return {"ok": True, "items": items}


def toggle_affiliate(name: str, enabled: bool) -> Dict[str, Any]:
    with connect() as cx:
        cur = cx.execute(
            "UPDATE affiliates SET enabled=?, mtime=? WHERE name=?",
                (1 if enabled else 0, time(), name),
                )
        cx.commit()
        changed = cur.rowcount
    return {"ok": changed > 0, "changed": changed}


async def validate_url(url: str, timeout_s: float = 10.0) -> Dict[str, Any]:
    """
    Reachability check using HEAD; falls back to GET when needed.
    """
    async with httpx.AsyncClient(follow_redirects = True, timeout = timeout_s) as client:
        try:
            r = await client.head(url)
            code = r.status_code
            ok = 200 <= code < 400
            if not ok:
                r2 = await client.get(url)
                code = r2.status_code
                ok = 200 <= code < 400
            return {"ok": ok, "status": code}
        except Exception as e:
            return {"ok": False, "error": str(e)}
