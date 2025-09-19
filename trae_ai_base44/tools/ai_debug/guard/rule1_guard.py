#!/usr/bin/env python3
import re
import sys
import pathlib

BANNED = [
    r"production",
    r"simulation",
    r"placeholder",
    r"theoretical",
    r"demo",
    r"mock",
    r"fake",
    r"sample",
    r"test",
]

SKIP_DIRS = {
    ".git",
    "node_modules",
    "venv",
    "venv_stable",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    "build",
    "dist",
    ".next",
}
INCLUDE_EXT = {
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".json",
    ".yml",
    ".yaml",
    ".md",
    ".toml",
    ".ini",
    ".sh",
    ".txt",
    ".go",
    ".rs",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".html",
    ".css",
}

root = pathlib.Path(".").resolve()
regex = re.compile(r"\\b(" + "|".join(BANNED) + r")\\b", re.IGNORECASE)

violations = []

for p in root.rglob("*"):
    if any(part in SKIP_DIRS for part in p.parts):
        continue
    if not p.is_file():
        continue
    if p.suffix.lower() not in INCLUDE_EXT:
        continue
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    for i, line in enumerate(text.splitlines(), 1):
        if regex.search(line):
            violations.append((str(p.relative_to(root)), i, line.strip()))

if violations:
    print("Rule-1 vocabulary violations found:")
    for path, line_no, line in violations[:200]:
        print(f"{path}:{line_no}: {line}")
    print(f"Total: {len(violations)}")
    sys.exit(1)
else:
    print("Rule-1 vocabulary check: clean.")
