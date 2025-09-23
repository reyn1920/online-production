#!/usr/bin/env python3
"""Basic audit: list top-level Python files and check imports."""
from pathlib import Path
import ast

def audit(root: Path):
  for p in root.glob('**/*.py'):
    try:
      tree = ast.parse(p.read_text())
    except Exception:
      continue
    imports = [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module]
    if imports:
      print(p, imports[:3])

if __name__ == '__main__':
  audit(Path('.'))
#!/usr/bin/env python3
"""
UPR auditor: two-pass routine aligned with your UPR rule.
Pass 1: format & quick lint
Pass 2: guard + normalizer + format repeat
Does not delete or rename anything.
"""
import argparse, os, subprocess, sys

def run(cmd: list) -> int:
    print("+", " ".join(cmd))
    try:
        return os.spawnvp(os.P_WAIT, cmd[0], cmd)
    except Exception:
        print("[UPR] tool missing or not runnable, skipping gracefully:", cmd[0])
        return 0

def pass1():
    run(["ruff", "check", "--fix", "."])
    run(["black", "."])

def pass2():
    run([sys.executable, "-u", "tools/rule1_guard.py", "--fail-on-hit"])
    run([sys.executable, "-u", "tools/syntax_normalizer.py"])
    run(["ruff", "check", "--fix", "."])
    run(["black", "."])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=["pass1","pass2"], default="pass1")
    args = ap.parse_args()
    if args.mode == "pass1":
        pass1()
    else:
        pass2()
    print("[UPR] complete:", args.mode)

if __name__ == "__main__":
    main()
