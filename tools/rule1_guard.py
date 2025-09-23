#!/usr/bin/env python3
"""Scan new files for banned vocabulary and write a report."""
import sys
from pathlib import Path

BANNED = [
  "production", "Production", "PRODUCTION", "simulation", "placeholder",
  "theoretical", "demo", "mock", "fake", "sample", "test"
]

def scan(root: Path):
  hits = []
  for p in root.rglob('*'):
    if p.suffix in ('.py', '.ts', '.tsx', '.js', '.jsx', '.json', '.md'):
      try:
        s = p.read_text(errors='ignore')
      except Exception:
        continue
      for b in BANNED:
        if b in s:
          hits.append((str(p), b))
  return hits

if __name__ == '__main__':
  root = Path('.')
  hits = scan(root)
  out = Path('rule1_guard_report.txt')
  with out.open('w') as f:
    if not hits:
      f.write('No hits\n')
      print('No hits')
    else:
      for p,b in hits:
        f.write(f"{p}: {b}\n")
      print(f"Found {len(hits)} hits, written to {out}")
#!/usr/bin/env python3
"""
Rule-1 guard: scans the tree and reports banned words. Exits 1 if --fail-on-hit.
This script avoids renaming or deleting any file; it only reports and exits code.
"""
import argparse, os, sys, re, json, pathlib

BANNED = [
    "production", "Production", "PRODUCTION",
    "simulation", "placeholder", "theoretical",
    "demo", "mock", "fake", "sample", "test"
]

SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", ".mypy_cache", ".ruff_cache", ".pytest_cache"}

def scan(root: str):
    hits = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fname in filenames:
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read()
                for word in BANNED:
                    for m in re.finditer(re.escape(word), text):
                        line = text.count("\n", 0, m.start()) + 1
                        hits.append({"file": fpath, "word": word, "line": line})
            except Exception:
                pass
    return hits

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fail-on-hit", action="store_true")
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    results = scan(args.root)
    out_dir = pathlib.Path("_trae/reports")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "rule1_guard.json"
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"[Rule-1] scanned, hits: {len(results)} -> {out_file}")
    if args.fail_on_hit and results:
        sys.exit(1)

if __name__ == "__main__":
    main()
