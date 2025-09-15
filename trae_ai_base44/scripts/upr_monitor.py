from __future__ import annotations

import subprocess
from collections.abc import Sequence

def run(cmd: Sequence[str]) -> int:
    """Run a command and stream output; return exit code."""
    proc = subprocess.run(list(cmd), check=False)
    return int(proc.returncode)

def main() -> int:
    # example heartbeat command; adjust to your real target
    return run(("python", "-V"))

if __name__ == "__main__":
    raise SystemExit(main())