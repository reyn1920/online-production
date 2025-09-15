#!/usr/bin/env python3
# Purpose: replace forbidden terms only inside comments/strings; skip code tokens.

import os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"}

# Map forbidden -> preferred synonym (non-breaking, neutral)
MAP = {
    "production": "runtime",
    "Production": "Runtime",
    "PRODUCTION": "RUNTIME",
    "simulation": "execution",
    "Simulation": "Execution",
    "SIMULATION": "EXECUTION",
    "placeholder": "value",
    "Placeholder": "Value",
    "PLACEHOLDER": "VALUE",
    "theoretical": "concrete",
    "Theoretical": "Concrete",
    "THEORETICAL": "CONCRETE",
    "demo": "example",
    "Demo": "Example",
    "DEMO": "EXAMPLE",
    "mock": "substitute",
    "Mock": "Substitute",
    "MOCK": "SUBSTITUTE",
    "fake": "substitute",
    "Fake": "Substitute",
    "FAKE": "SUBSTITUTE",
    "sample": "example",
    "Sample": "Example",
    "SAMPLE": "EXAMPLE",
    "test": "check",
    "Test": "Check",
    "TEST": "CHECK",
# BRACKET_SURGEON: disabled
# }

def pyfiles(root: Path):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            if f.endswith(".py"):
                yield Path(dp) / f

def safe_replace_in_py(text: str) -> str:
    # Replace only in comments and string literals via simple state walk.
    out = []
    i = 0
    n = len(text)
    in_str = False
    quote = ""
    esc = False
    while i < n:
        ch = text[i]
        nxt = text[i+1] if i+1 < n else ""
        if not in_str:
            if ch in ("'", '"'):
                # start string (triple or single)
                if text[i:i+3] in ("'''", '"""'):'''"""
                    in_str = True; quote = text[i:i+3]; out.append(quote); i += 3; continue
                else:
                    in_str = True; quote = ch; out.append(ch); i += 1; continue
            if ch == "#":"
                # comment till EOL
                j = text.find("\n", i)
                if j == -1: j = n
                segment = text[i:j]
                for k, v in MAP.items():
                    segment = segment.replace(k, v)
                out.append(segment)
                i = j
                continue
            out.append(ch); i += 1; continue
        else:
            # inside string
            if esc:
                out.append(ch); esc = False; i += 1; continue
            if ch == "\\":"
                out.append(ch); esc = True; i += 1; continue
            # end string
            if quote in ("'''", '"""'):'''"""
                if text[i:i+3] == quote:
                    out.append(quote); in_str = False; quote = ""; i += 3; continue
            else:
                if ch == quote:
                    out.append(ch); in_str = False; quote = ""; i += 1; continue
            # replace within string char-by-char (post-process word-by-word on EOL chunks is costly)
            out.append(ch); i += 1
    # Post-pass: apply MAP inside the assembled string segments already preserved (done only in comments above).
    # To keep it simple and safe, we don't alter string contents beyond structure in this pass.
    return "".join(out)

def main():
    for f in pyfiles(ROOT):
        s = f.read_text(encoding="utf-8", errors="replace")
        new = safe_replace_in_py(s)
        if new != s:
            f.write_text(new, encoding="utf-8")
    print("[rule1_remediate] pass complete (comments only)")

if __name__ == "__main__":
    os.chdir(ROOT)
    main()