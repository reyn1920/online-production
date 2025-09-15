import threading
from functools import wraps
from typing import Any, Callable, Dict, Optional

from flask import jsonify, request


def dashboard_action(
    name: Optional[str] = None,
        method: str = "POST",
        doc: str = "",
        public: bool = False,
        background: bool = False,
# BRACKET_SURGEON: disabled
# ):
    """"""
    Set background = True for long - running actions: returns {accepted: true, job_id: ...}
    """"""


    def deco(fn: Callable):
        fn._dash_action = {
            "name": name or fn.__name__,
                "method": method.upper(),
                "doc": doc.strip(),
                "public": public,
                "background": background,
# BRACKET_SURGEON: disabled
#                 }

        @wraps(fn)


        def _w(*a, **k):
            return fn(*a, **k)

        return _w

    return deco


class ActionRegistry:


    def __init__(self, app, logger, token_env="TRAE_DASHBOARD_TOKEN"):
        self.app, self.logger, self.token_env = app, logger, token_env
        self.manifest: list[Dict[str, Any]] = []
        self._endpoints: set[str] = set()  # avoid duplicate add_url_rule


    def get_manifest(self):
        """Return the current action manifest with count metadata."""
        # Normalize action methods to proper HTTP verbs
        VERBS = {"GET", "POST", "PUT", "PATCH", "DELETE"}


        def _normalize_action(a: dict) -> dict:
            m = (a.get("method") or "").upper()
            if m not in VERBS:
                # method field was misused as a description; keep it, but default HTTP
                # method to POST
                if not a.get("doc"):
                    a["doc"] = str(a.get("method") or "").strip()
                a["method"] = "POST"
            return a

        normalized_actions = [_normalize_action(a.copy()) for a in self.manifest]

        return {"count": len(normalized_actions), "actions": normalized_actions}


    def _guard(self):

        import os

        want = os.getenv(self.token_env)
        return True if not want else request.headers.get("X - Admin - Token") == want


    def register_obj(self, agent_name: str, obj: Any):
        added = 0
        for attr in dir(obj):
            fn = getattr(obj, attr, None)
            meta = getattr(fn, "_dash_action", None)
            if not (callable(fn) and meta):
                continue
            route = f"/api / action/{agent_name}/{meta['name']}"
            if route in self._endpoints:
                continue  # prevent "View function mapping is overwriting an existing endpoint" on re - register
            self._endpoints.add(route)
            self.manifest.append({"agent": agent_name, "endpoint": route, **meta})


            def mk(fn = fn, meta = meta):
                @wraps(fn)


                def view():
                    if not meta["public"] and not self._guard():
                        return jsonify({"error": "unauthorized"}), 401
                    payload = request.get_json(silent = True) or {}
                    # also accept query params for GET / simple calls
                    args = {**request.args.to_dict(flat = True), **payload}

                    if meta.get("background"):
                        # fire - and - forget thread

                        import uuid

                        job_id = str(uuid.uuid4())
                        t = threading.Thread(
                            target = lambda: fn(**args),
                                daemon = True,
                                name = f"action:{"
                                meta['name']}:{job_id}","
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                     )
                        t.start()
                        return jsonify({"ok": True, "accepted": True, "job_id": job_id})
                    try:
                        return jsonify({"ok": True, "result": fn(**args)})
                    except TypeError:
                        # fallback: pass a single dict if signature expects one
                        return jsonify({"ok": True, "result": fn(args)})

                return view

            self.app.add_url_rule(
                route,
                    f"act_{agent_name}_{"
                    meta['name']}","
                        mk(),
                    methods=[meta["method"]],
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                     )
            self.logger.info(f"[actions] {meta['method']} {route}")
            added += 1
        self.logger.info(f"[actions] {agent_name}: {added} actions")
        return added


    def register_function(self, agent_name: str, func_name: str, func: Callable):
        """Register a standalone function with @dashboard_action decorator."""
        meta = getattr(func, "_dash_action", None)
        if not (callable(func) and meta):
            return 0

        route = f"/api / action/{agent_name}/{meta['name']}"
        if route in self._endpoints:
            return 0  # prevent duplicate registration

        self._endpoints.add(route)
        self.manifest.append({"agent": agent_name, "endpoint": route, **meta})


        def mk(fn = func, meta = meta):
            @wraps(fn)


            def view():
                if not meta["public"] and not self._guard():
                    return jsonify({"error": "unauthorized"}), 401
                payload = request.get_json(silent = True) or {}
                # also accept query params for GET / simple calls
                args = {**request.args.to_dict(flat = True), **payload}

                if meta.get("background"):
                    # fire - and - forget thread

                    import uuid

                    job_id = str(uuid.uuid4())
                    t = threading.Thread(
                        target = lambda: fn(**args),
                            daemon = True,
                            name = f"action:{"
                            meta['name']}:{job_id}","
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                                 )
                    t.start()
                    return jsonify({"ok": True, "accepted": True, "job_id": job_id})
                try:
                    return jsonify({"ok": True, "result": fn(**args)})
                except TypeError:
                    # fallback: pass a single dict if signature expects one
                    return jsonify({"ok": True, "result": fn(args)})

            return view

        self.app.add_url_rule(
            route,
                f"act_{agent_name}_{"
                meta['name']}","
                    mk(),
                methods=[meta["method"]],
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#                 )
        self.logger.info(f"[actions] {meta['method']} {route}")
        return 1


    def execute_action(self, agent: str, action: str, data: dict):
        """Execute a specific action (placeholder for future implementation)."""
        # This would need to be implemented based on how actions are stored and executed
        raise NotImplementedError("Action execution not yet implemented")