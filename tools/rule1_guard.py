#!/usr/bin/env python3
""""""
Rule-1 Guard — blocks forbidden tokens in code/comments/strings.
If found, writes a violation report and exits non-zero if run with --strict.
""""""
import os, re, sys, json, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGDIR = ROOT / "tools" / "logs"
LOGDIR.mkdir(parents=True, exist_ok=True)

FORBIDDEN = [
    "production", "Production", "PRODUCTION",
    "simulation", "Simulation", "SIMULATION",
    "placeholder", "Placeholder", "PLACEHOLDER",
    "theoretical", "Theoretical", "THEORETICAL",
    "demo", "Demo", "DEMO",
    "mock", "Mock", "MOCK",
    "fake", "Fake", "FAKE",
    "sample", "Sample", "SAMPLE",
    "test", "Test", "TEST",
# BRACKET_SURGEON: disabled
# ]

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"}

def iter_text_files(root: Path):
    exts = {".py", ".md", ".txt", ".json", ".yml", ".yaml", ".toml", ".cfg", ".ini"}
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if Path(f).suffix in exts:
                yield Path(dp) / f

def main():
    violations = []
    for p in iter_text_files(ROOT):
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for term in FORBIDDEN:
            if term in txt:
                for i, line in enumerate(txt.splitlines(), 1):
                    if term in line:
                        violations.append({"file": str(p.relative_to(ROOT)), "line": i, "term": term, "snippet": line.strip()})
    report = {
        "violations": violations,
        "count": len(violations),
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
# BRACKET_SURGEON: disabled
#     }
    (LOGDIR / "rule1_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    if "--strict" in sys.argv and violations:
        print(f"[Rule1] violations={len(violations)} (strict)")
        sys.exit(2)
    print(f"[Rule1] violations={len(violations)} report={LOGDIR/'rule1_report.json'}")

if __name__ == "__main__":
    os.chdir(ROOT)
    main()