#!/usr/bin/env python3
"""
PyAudit — fast, local parser sweep with precise error capture.
Add-only, zero external deps. Writes JSON + MD reports under tools/logs/.
Rule-1 note: this file avoids banned vocabulary in comments/strings.
"""
import sys, os, json, time, traceback, io, tokenize
from pathlib import Path
from fnmatch import fnmatch

ROOT = Path(__file__).resolve().parents[1]
LOGDIR = ROOT / "tools" / "logs"
LOGDIR.mkdir(parents=True, exist_ok=True)

# Enhanced exclusion patterns
EXCLUDE_DIRS = {"venv", "venv_stable", ".venv", ".venv_base44", "__pycache__", "site-packages", ".git", "node_modules", "dist", "build"}
SKIP_PATTERNS = os.getenv("BASE44_SKIP_GLOBS", "venv*,.venv*,**/site-packages/**,**/__pycache__/**").split(",")

def should_skip(path_parts: list[str]) -> bool:
    return any(part in EXCLUDE_DIRS for part in path_parts) or "site-packages" in path_parts

def skip_by_glob(p: str) -> bool:
    return any(fnmatch(p, pat) for pat in SKIP_PATTERNS)

def iter_py_files(root: Path):
    for dp, dn, fn in os.walk(root):
        parts = Path(dp).parts
        if should_skip(list(parts)):
            continue
        dn[:] = [d for d in dn if not should_skip(list(Path(dp, d).parts))]
        for f in fn:
            if f.endswith(".py"):
                file_path = Path(dp) / f
                if not skip_by_glob(str(file_path)):
                    yield file_path

def try_compile(path: Path):
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        compile(src, str(path), "exec")
        return None
    except SyntaxError as e:
        return {
            "file": str(path.relative_to(ROOT)),
            "line": e.lineno,
            "offset": e.offset,
            "msg": e.msg,
            "text": (e.text or "").rstrip("\n"),
# BRACKET_SURGEON: disabled
#         }
    except Exception as e:
        return {
            "file": str(path.relative_to(ROOT)),
            "line": None,
            "offset": None,
            "msg": f"NonSyntax:{e.__class__.__name__}: {e}",
            "text": "",
# BRACKET_SURGEON: disabled
#         }

def main():
    t0 = time.time()
    errors = []
    total = 0
    for pf in iter_py_files(ROOT):
        total += 1
        err = try_compile(pf)
        if err:
            errors.append(err)
    out_json = {
        "scanned_files": total,
        "error_count": len(errors),
        "errors": errors,
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
# BRACKET_SURGEON: disabled
#     }
    (LOGDIR / "pyaudit_report.json").write_text(json.dumps(out_json, indent=2), encoding="utf-8")
    # Pretty MD
    lines = [
        "# PyAudit Report","
        f"- Scanned: {total}",
        f"- Errors: {len(errors)}",
        "",
        "| # | File | Line | Col | Message | Snippet |","
        "|---|------|------|-----|---------|---------|",
# BRACKET_SURGEON: disabled
#     ]
    for i, e in enumerate(errors, 1):
        snippet = (e["text"] or "").replace("|", "¦").strip()
        lines.append(f"| {i} | {e['file']} | {e['line'] or ''} | {e['offset'] or ''} | {e['msg']} | `{snippet}` |")
    (LOGDIR / "pyaudit_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"[PyAudit] files={total} errors={len(errors)} took={time.time()-t0:.2f}s")
    print(f"JSON: {LOGDIR/'pyaudit_report.json'}")
    print(f"MD  : {LOGDIR/'pyaudit_report.md'}")

if __name__ == "__main__":
    os.chdir(ROOT)
    main()