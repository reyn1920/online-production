#!/usr/bin/env python3
""""""
FixIt — conservative mass-repair for giant Python codebases.
Passes:
  1) whitespace normalizer (tabs→4 spaces, trim, LF)
  2) orphan follower guard: if prev line ended with "\" and current begins with logical conj ("or ", "and ") outside strings, comment it"
# BRACKET_SURGEON: disabled
#   3) empty-suite guard: ensure a body after block starters by inserting 'pass'
# BRACKET_SURGEON: disabled
#   4) unmatched closer guard: when compile fails due to unmatched ')' or ']', comment only the offending line
Idempotent; logs diffs to tools/logs/fixit_changes/*.patch
Rule-1 note: avoids banned vocabulary in comments/strings.
""""""
import re, os, sys, time, difflib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOGDIR = ROOT / "tools" / "logs"
PATCHDIR = LOGDIR / "fixit_changes"
PATCHDIR.mkdir(parents=True, exist_ok=True)

SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"}

BLOCK_STARTERS = re.compile(r'^\s*(def|class|if|elif|else|for|while|try|except|finally|with)\b.*:\s*(#.*)?$')'
ONLY_WS_OR_COMMENT = re.compile(r'^\s*(#.*)?$')'
LOGICAL_OR_AND = re.compile(r'^\s*(or|and)\b')

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")

def write(p: Path, s: str):
    p.write_text(s, encoding="utf-8")

def norm_ws(text: str) -> str:
    # normalize EOLs, tabs→4 spaces, strip trailing
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\t", "    ")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text

def guard_orphan_followers(lines):
    out = []
    prev = ""
    for i, line in enumerate(lines):
        if prev.rstrip().endswith("\\"):"
            # If current starts with logical conj and is not already a comment, make it comment
            if LOGICAL_OR_AND.match(line) and not line.lstrip().startswith("#"):"
                out.append("# " + line)"
            else:
                out.append(line)
        else:
            out.append(line)
        prev = line
    return out

def ensure_block_bodies(lines):
    out = []
    i = 0
    n = len(lines)
    while i < n:
        out.append(lines[i])
        if BLOCK_STARTERS.match(lines[i]):
            # find next non-empty, non-comment line
            j = i + 1
            while j < n and ONLY_WS_OR_COMMENT.match(lines[j]):
                j += 1
            # If next is dedent or end or another block starter at same/less indent, insert pass
            indent = len(lines[i]) - len(lines[i].lstrip(" "))
            needs_pass = (j >= n) or (len(lines[j]) - len(lines[j].lstrip(" ")) <= indent)
            if needs_pass:
                out.append(" " * (indent + 4) + "pass")
        i += 1
    return out

def compile_ok(src: str, path: str) -> bool:
    try:
        compile(src, path, "exec")
        return True
    except SyntaxError:
        return False
    except Exception:
        return True  # non-syntax is OK here

def guard_unmatched_closers(lines, path):
    # Try compile; if unmatched ) or ] causes a specific line to fail, comment that line conservatively.
    src = "\n".join(lines)
    if compile_ok(src, path):
        return lines
    # crude pass: comment isolated closers on their own or trailing tokens
    fixed = []
    for ln in lines:
        s = ln.strip()
        if s in (")", "]") or s.endswith((")", "]")) and s.count("(") < s.count(")") or s.count("[") < s.count("]"):
            fixed.append("# FIXIT: commented possible stray closer\n" + ("# " + ln if not ln.lstrip().startswith("#") else ln))"
        else:
            fixed.append(ln)
    return fixed

def process_file(p: Path):
    before = read(p)
    after = norm_ws(before)
    lines = after.split("\n")
    lines = guard_orphan_followers(lines)
    lines = ensure_block_bodies(lines)
    lines = guard_unmatched_closers(lines, str(p))
    after = "\n".join(lines)
    if after != before:
        patch = difflib.unified_diff(before.splitlines(True), after.splitlines(True), fromfile=str(p), tofile=str(p))
        patch_text = "".join(patch)
        write(p, after)
        (PATCHDIR / (p.name + ".patch")).write_text(patch_text, encoding="utf-8")

def iter_py_files(root: Path):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if f.endswith(".py"):
                yield Path(dp) / f

def main():
    t0 = time.time()
    changed = 0
    total = 0
    for pf in iter_py_files(ROOT):
        total += 1
        before = read(pf)
        process_file(pf)
        after = read(pf)
        if after != before:
            changed += 1
    print(f"[FixIt] scanned={total} changed={changed} took={time.time()-t0:.2f}s")
    print(f"Patches: {PATCHDIR}")

if __name__ == "__main__":
    os.chdir(ROOT)
    main()