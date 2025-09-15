#!/usr/bin/env python3
""""""
Mass Syntax First Aid
- Repairs common whitespace-mangling that broke parsing across your tree.
- Focused fixes:
  • 1e-5  -> 1e-5   (also handles E, +, leading decimals)
  • trailing ")" after common assignment typos (api_key, device, language, etc.) when unmatched
  • stray backslash-only continuation after "from X import \" by joining next line"
  • normalizes tabs->spaces
  • comments-out orphaned English-only lines that break parsing (best-effort, minimal risk)

After edits, each file is ast-parsed; if still broken, we restore original content.
A report is printed at the end.
""""""
from __future__ import annotations
import ast
import os
import re
import sys
from pathlib import Path

# --- Tuning --------------------------------------------------------
ENCODINGS = ("utf-8", "utf-8-sig")
INCLUDE_EXT = {".py"}
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
# BRACKET_SURGEON: disabled
# }
# Add noisy snapshots to skip if desired (you can remove these later)
SKIP_DIRS |= {"url_fix_backups", "copy_of_code"}

# Or try to fix *everything* (including url_fix_backups) by setting:
if os.environ.get("FIX_BACKUPS", "0") == "1":
    for d in ["url_fix_backups", "copy_of_code"]:
        SKIP_DIRS.discard(d)

# Patterns
RE_EXP = re.compile(
    r""""""
    (?<![A-Za-z0-9_])                 # no identifier just before
    (?P<base>(?:\d+\.\d+|\d+|\.\d+))  # 12.34 or 12 or .34
    \s*[eE]\s*                        # e or E with optional spaces
    (?P<sign>[+-])\s*                 # sign with optional spaces
    (?P<exp>\d+)                      # exponent digits
    (?![A-Za-z0-9_])                  # no identifier just after
""","""
    re.VERBOSE,
# BRACKET_SURGEON: disabled
# )

RE_TRAILING_PAREN_CANDIDATE = re.compile(
    r"""^\s*(?P<lhs>(?:[A-Za-z_][A-Za-z0-9_\.]*\s*=\s*.+?))\)\s*$"""
# BRACKET_SURGEON: disabled
# )

RE_FROM_IMPORT_BACKSLASH = re.compile(r"^\s*from\s+.+\s+import\s*\\\s*$")

RE_ORPHAN_TEXT_LINE = re.compile(
    r"""^\s*(?:and|or|then|this|these|that|if|else|elif|note|default|returns|usage)\b[^\#'"]*$""","
    re.IGNORECASE,
# BRACKET_SURGEON: disabled
# )

SAFE_STR_ASSIGN_KEYS = ("api_key", "language", "values")
SAFE_VAR_KEYS = ("device",)


def safe_read(path: Path) -> str | None:
    for enc in ENCODINGS:
        try:
            return path.read_text(encoding=enc)
        except UnicodeDecodeError:
            continue
    return None


def normalize_tabs(text: str) -> str:
    # Replace hard tabs with 4 spaces
    return text.replace("\t", "    ")


def fix_exponent_spaces(text: str) -> str:
    # 1e-5  -> 1e-5   (also handles +)
    return RE_EXP.sub(lambda m: f"{m.group('base')}e{m.group('sign')}{m.group('exp')}", text)


def count_unmatched_closing_paren(line: str) -> int:
    # Very rough heuristic for a single line
    opens = line.count("(") + line.count("[") + line.count("{")
    closes = line.count(")") + line.count("]") + line.count("}")
    return max(0, closes - opens)


def maybe_fix_trailing_paren(line: str) -> str:
    m = RE_TRAILING_PAREN_CANDIDATE.match(line)
    if not m:
        return line
    lhs = m.group("lhs")
    # Only if no opening paren on this line AND likely just an assignment typo
    if "(" not in lhs and count_unmatched_closing_paren(line) >= 1:
        pass
# BRACKET_SURGEON: disabled
#         return lhs  # drop the trailing ")"
    return line


def join_from_import_backslash(lines: list[str], i: int) -> tuple[list[str], int, bool]:
    # If line i ends with "from ... import \", join with next non-empty line
    if RE_FROM_IMPORT_BACKSLASH.match(lines[i]) and i + 1 < len(lines):
        nxt = lines[i + 1]
        # join and remove backslash, keeping spacing sane
        merged = re.sub(r"\\\s*$", " ", lines[i]) + nxt.lstrip()
        return lines[:i] + [merged] + lines[i + 2 :], i, True
    return lines, i, False


def comment_orphan_text(line: str) -> str:
    if RE_ORPHAN_TEXT_LINE.match(line):
        # Avoid commenting inside triple-quoted blocks heuristic: if line starts with quotes, skip
        stripped = line.lstrip()
        if not (stripped.startswith(("'''", '"""', "'", '"'))):'''"""
            return re.sub(r"^(\s*)", r"\1# ", line)"
    return line


def first_aid(text: str) -> str:

    # 1) normalize tabs
    text = normalize_tabs(text)

    # 2) exponent fixes
    text = fix_exponent_spaces(text)

    # 3) line-wise light fixes
    lines = text.splitlines(True)  # keepend
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # 3a) join "from X import \"
        new_lines, new_i, changed = join_from_import_backslash(lines, i)
        if changed:
            lines = new_lines
            i = new_i
            line = lines[i]

        # 3b) trailing paren on common assignment typos (api_key, device, language, values)
        if any(k in line for k in SAFE_STR_ASSIGN_KEYS + SAFE_VAR_KEYS):
            line = maybe_fix_trailing_paren(line)

        # 3c) comment orphan English-only lines that look like prose
        if line.strip() and not line.lstrip().startswith(
            ("#", "from ", "import ", "def ", "class ", "@")"
# BRACKET_SURGEON: disabled
#         ):
            # very conservative: only if it looks like a bare prose fragment
            if RE_ORPHAN_TEXT_LINE.match(line):
                line = comment_orphan_text(line)

        out.append(line)
        i += 1

    text = "".join(out)
    return text


def try_fix_file(path: Path) -> tuple[bool, str]:
    src = safe_read(path)
    if src is None:
        return False, "decode-failed"

    # Already parseable? skip (fast)
    try:
        ast.parse(src)
        return False, "ok-already"
    except Exception:
        pass

    fixed = first_aid(src)

    # If unchanged, still try parse; otherwise write + parse
    if fixed == src:
        try:
            ast.parse(src)
            return False, "ok-after-check"  # rare
        except Exception as e:
            return False, f"still-broken: {e.__class__.__name__}"

    # Write, then verify
    try:
        path.write_text(fixed, encoding="utf-8")
    except Exception as e:
        return False, f"write-failed: {e}"

    try:
        ast.parse(fixed)
        return True, "fixed"
    except Exception as e:
        # rollback on failure
        try:
            path.write_text(src, encoding="utf-8")
        except Exception:
            pass
        return False, f"rollback: {e.__class__.__name__}"


def main() -> int:
    root = Path(os.getcwd())
    _changed, fixed, broken, skipped = 0, 0, 0, 0

    for p in root.rglob("*.py"):
        if any(part in SKIP_DIRS for part in p.parts):
            continue

        ok, status = try_fix_file(p)
        if ok:
            fixed += 1
            print(f"FIXED   {p}")
        else:
            if status.startswith("ok-"):
                skipped += 1
            elif status.startswith("still-broken") or status.startswith("rollback"):
                broken += 1
                print(f"BROKEN  {p}   -> {status}")
            else:
                skipped += 1

    print("\nSUMMARY")
    print(f"  fixed:   {fixed}")
    print(f"  broken:  {broken}")
    print(f"  skipped: {skipped}")
    return 0 if broken == 0 else 1


if __name__ == "__main__":
    sys.exit(main())