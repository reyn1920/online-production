#!/usr/bin/env python3
"""
Lightweight logger tuner to reduce console noise from verbose frameworks.
Enabled by env: TRAE_QUIET_LOGS = 1 (default off).
"""

import logging
import os

TARGETS = [
    "socketio.server",  # "emitting event ..." spam
    "engineio.server",
    "werkzeug",  # request line spam
    "uvicorn.access",  # if applicable
]


def tune_chatty_loggers():
    if os.getenv("TRAE_QUIET_LOGS", "0") != "1":
        return
    for name in TARGETS:
        try:
            logging.getLogger(name).setLevel(logging.WARNING)
        except Exception:
            pass
    # Optional: keep your own app at INFO
    logging.getLogger("trae_ai").setLevel(logging.INFO)
