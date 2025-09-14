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
):
    """
    Set background = True for long-running actions: returns {accepted: true, job_id: ...}
    """

    def deco(fn: Callable):
        fn._dash_action = {
            "name": name or fn.__name__,
            "method": method.upper(),
            "doc": doc.strip(),
            "public": public,
            "background": background,
        }

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
        self._actions = {}  # Store registered actions

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
        return True if not want else request.headers.get("X-Admin-Token") == want

    def register_obj(self, agent_name: str, obj: Any):
        added = 0
        for attr in dir(obj):
            fn = getattr(obj, attr, None)
            meta = getattr(fn, "_dash_action", None)
            if not (callable(fn) and meta):
                continue
            route = f"/api/action/{agent_name}/{meta['name']}"
            if route in self._endpoints:
                continue  # prevent "View function mapping is overwriting an existing endpoint" on re-register
            self._endpoints.add(route)
            self.manifest.append({"agent": agent_name, "endpoint": route, **meta})

            def mk(fn=fn, meta=meta):
                @wraps(fn)
                def view():
                    if not meta["public"] and not self._guard():
                        return jsonify({"error": "unauthorized"}), 401
                    payload = request.get_json(silent=True) or {}
                    # also accept query params for GET/simple calls
                    args = {**request.args.to_dict(flat=True), **payload}

                    if meta.get("background"):
                        # fire-and-forget thread
                        import uuid

                        job_id = str(uuid.uuid4())
                        t = threading.Thread(
                            target=lambda: fn(**args),
                            daemon=True,
                            name=f"action:{meta['name']}:{job_id}",
                        )
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
                f"act_{agent_name}_{meta['name']}",
                mk(),
                methods=[meta["method"]],
            )
            self.logger.info(f"[actions] {meta['method']} {route}")
            added += 1
        self.logger.info(f"[actions] {agent_name}: {added} actions")
        return added

    def register_function(self, agent_name: str, func_name: str, func: Callable):
        """Register a standalone function with @dashboard_action decorator."""
        meta = getattr(func, "_dash_action", None)
        if not (callable(func) and meta):
            return 0

        route = f"/api/action/{agent_name}/{meta['name']}"
        if route in self._endpoints:
            return 0  # prevent duplicate registration

        self._endpoints.add(route)
        self.manifest.append({"agent": agent_name, "endpoint": route, **meta})

        def mk(fn=func, meta=meta):
            @wraps(fn)
            def view():
                if not meta["public"] and not self._guard():
                    return jsonify({"error": "unauthorized"}), 401
                payload = request.get_json(silent=True) or {}
                # also accept query params for GET/simple calls
                args = {**request.args.to_dict(flat=True), **payload}

                if meta.get("background"):
                    # fire-and-forget thread
                    import uuid

                    job_id = str(uuid.uuid4())
                    t = threading.Thread(
                        target=lambda: fn(**args),
                        daemon=True,
                        name=f"action:{meta['name']}:{job_id}",
                    )
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
            f"act_{agent_name}_{meta['name']}",
            mk(),
            methods=[meta["method"]],
        )
        self.logger.info(f"[actions] {meta['method']} {route}")
        return 1

    def execute_action(self, agent: str, action: str, data: dict):
        """Execute a specific action by calling the registered function."""
        try:
            # Find the action in the registry
            action_key = f"{agent}:{action}"
            if action_key not in self._actions:
                return {
                    "ok": False,
                    "error": f"Action {action} not found for agent {agent}",
                }

            # Execute the action
            result = self._actions[action_key](**data)
            return {"ok": True, "result": result}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_action_info(self, agent: str, action: str):
        """Get information about a specific action."""
        for item in self.manifest:
            if item.get("agent") == agent and item.get("name") == action:
                return {"ok": True, "action": item}
        return {"ok": False, "error": f"Action {action} not found for agent {agent}"}

    def list_actions(self, agent: str = None):
        """List all actions, optionally filtered by agent."""
        if agent:
            actions = [item for item in self.manifest if item.get("agent") == agent]
        else:
            actions = self.manifest

        return {"ok": True, "count": len(actions), "actions": actions}

    def clear_actions(self, agent: str = None):
        """Clear actions, optionally filtered by agent."""
        if agent:
            self.manifest = [item for item in self.manifest if item.get("agent") != agent]
            # Clear endpoints for this agent
            endpoints_to_remove = {ep for ep in self._endpoints if f"/api/action/{agent}/" in ep}
            self._endpoints -= endpoints_to_remove
        else:
            self.manifest.clear()
            self._endpoints.clear()
            self._actions.clear()

        return {
            "ok": True,
            "message": f"Actions cleared for {agent if agent else 'all agents'}",
        }
