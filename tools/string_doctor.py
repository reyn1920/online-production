#!/usr/bin/env python3
# Purpose: heal unterminated string literals (incl. f-strings) conservatively.
# Notes: add-only edits; avoids Rule-1 tokens in comments/strings.

import os, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"}

TRI = ("'''", '"""')'''

def pyfiles(root: Path):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            if f.endswith(".py"):
                yield Path(dp) / f

def balance_line_quotes(line: str) -> str:
    # Quick guard for triple quotes: if odd count of a triple, append one at end
    fixed = line
    for q in TRI:
        if fixed.count(q) % 2 != 0:
            fixed += q
            return fixed
    # Balance single/double if clearly unterminated and not a comment-only line
    if "#" in fixed:
        code = fixed.split("#", 1)[0]
    else:
        code = fixed
    singles = code.count("'") - code.count("\'")
    doubles = code.count('"') - code.count('\"')
    if singles % 2 != 0 and doubles % 2 == 0:
        fixed += "'"
    elif doubles % 2 != 0 and singles % 2 == 0:
        fixed += '"'
    return fixed

def fix_file(p: Path):
    s = p.read_text(encoding="utf-8", errors="replace")
    lines = s.replace("\r\n","\n").replace("\r","\n").split("\n")
    out = [balance_line_quotes(ln) for ln in lines]
    new = "\n".join(out)
    if new != s:
        p.write_text(new, encoding="utf-8")

def main():
    for f in pyfiles(ROOT):
        fix_file(f)
    print("[string_doctor] pass complete")

if __name__ == "__main__":
    os.chdir(ROOT)
    main()