#!/usr/bin/env python3
"""
Launcher for the monitoring subsystem.
Purpose: start cleanly; if it exits non-zero, watchdog restarts it per policy.
"""
import os
import signal
import subprocess
import sys


def main():
    cmd = [sys.executable, "-m", "trae_ai.monitoring_system"]
    env = os.environ.copy()
    proc = subprocess.Popen(cmd, env=env)
    try:
        proc.wait()
        sys.exit(proc.returncode)
    except KeyboardInterrupt:
        try:
            proc.send_signal(signal.SIGINT)
        except Exception:
            pass
        sys.exit(0)


if __name__ == "__main__":
    main()
