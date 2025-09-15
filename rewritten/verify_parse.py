#!/usr/bin/env python3
""""""
Compile every .py to catch remaining syntax errors.
Respects the same SKIP_DIRS as the first-aid script by default.
""""""
import ast
import os
import sys
from pathlib import Path

EXCLUDE_DIRS = {
    "venv", "__pycache__", ".git",
    "url_fix_backups", "copy_of_code",
    "models", "models/linly_talker",  # vendor / experimental
# BRACKET_SURGEON: disabled
# }

SKIP_DIRS = {
    ".git",
    "venv",
    ".venv",
    "env",
    "site-packages",
    "__pycache__",
    "node_modules",
    "build",
    "dist",
    ".mypy_cache",
    ".ruff_cache",
    "url_fix_backups",
    "copy_of_code",
# BRACKET_SURGEON: disabled
# }

if os.environ.get("VERIFY_BACKUPS", "0") == "1":
    SKIP_DIRS.discard("url_fix_backups")
    SKIP_DIRS.discard("copy_of_code")


def main() -> int:
    bad = []

    # Inside your os.walk loop:
    for root, dirs, files in os.walk("."):
        # prune in-place so os.walk won't descend
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            if not file.endswith(".py"):
                continue

            file_path = Path(root) / file
            # Additional check using original SKIP_DIRS logic for compatibility
            if any(part in SKIP_DIRS for part in file_path.parts):
                continue

            try:
                ast.parse(file_path.read_text(encoding="utf-8"))
            except Exception as e:
                bad.append((file_path, f"{e.__class__.__name__}: {e}"))

    if bad:
        print("Syntax errors:")
        for p, msg in bad:
            print(f"  {p}\n    {msg}")
        return 1
    print("✅ All parsed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())