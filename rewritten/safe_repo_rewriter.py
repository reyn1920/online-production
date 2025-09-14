#!/usr/bin/env python3
from __future__ import annotations
import argparse, ast, json, pathlib, re, fnmatch

ROOT = pathlib.Path(".").resolve()
OUT  = ROOT / "rewritten"

IGNORE = []
if (ROOT / ".rewriteignore").exists():
    IGNORE = [p.strip() for p in open(ROOT / ".rewriteignore", encoding="utf-8").read().splitlines()
              if p.strip() and not p.startswith("#")]

def ignored(path: str) -> bool:
    norm = path.replace("\\", "/")
    return any(fnmatch.fnmatch(norm, pat) for pat in IGNORE)

def normalize_newlines(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")

def tabs_to_spaces(s: str) -> str:
    return re.sub(r"^(?P<i>\t+)", lambda m: "    " * len(m.group("i")), s, flags=re.M)

def ensure_newline_eof(s: str) -> str:
    return s if s.endswith("\n") else s + "\n"

def try_parse(src: str, filename: str):
    try:
        ast.parse(src, filename=filename)
        return True, None
    except SyntaxError as e:
        return False, e

def close_unterminated_triple_quotes(s: str):
    actions = []
    for triple in ("'''", '"""'):
        if s.count(triple) % 2 == 1:
            s += triple + "\n"
            actions.append(f"closed {triple} at EOF")
    return s, actions

def balance_brackets(s: str):
    actions = []
    open_count = {"(":0, "[":0, "{":0}
    close_for = {")":"(", "]":"[", "}":"{"}
    rev = {"(" : ")", "[" : "]", "{" : "}"}
    for ch in s:
        if ch in open_count:
            open_count[ch] += 1
        elif ch in close_for:
            open_count[close_for[ch]] -= 1
    closers = []
    for k, v in open_count.items():
        if v > 0:
            closers.extend(rev[k] * v)
    if closers:
        s += "".join(closers) + "\n"
        actions.append("appended closers at EOF: " + "".join(closers))
    return s, actions

def fix_unterminated_single_line(s: str, lineno: int):
    lines = s.split("\n")
    if 1 <= lineno <= len(lines):
        L = lines[lineno-1]
        for q in ('"', "'"):
            count = len(re.findall(rf"(?<!\\){re.escape(q)}", L))
            if count % 2 == 1:
                lines[lineno-1] = L + q
                return "\n".join(lines), True
    return s, False

def comment_out_line(s: str, lineno: int, reason: str):
    lines = s.split("\n")
    if 1 <= lineno <= len(lines):
        orig = lines[lineno-1]
        marker = f'"""[PRESERVED-BROKEN-LINE] {reason[:120]}"""\n# ' + orig
        lines[lineno-1] = marker
    return "\n".join(lines)

def process_file(src: pathlib.Path, comment_on_fail: bool):
    rel = src.relative_to(ROOT)
    out = OUT / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = src.read_text(encoding="utf-8", errors="replace")
    meta = {"file": str(rel).replace("\\","/"), "actions": []}

    s = normalize_newlines(raw)
    if s != raw: meta["actions"].append("normalize_newlines")
    s2 = tabs_to_spaces(s)
    if s2 != s: meta["actions"].append("tabs_to_spaces")
    s = ensure_newline_eof(s2)

    ok, err = try_parse(s, str(rel))
    if ok:
        out.write_text(s, encoding="utf-8"); meta["result"] = "parsed"; return meta

    s, a1 = close_unterminated_triple_quotes(s); meta["actions"].extend(a1)
    s, a2 = balance_brackets(s); meta["actions"].extend(a2)
    s = ensure_newline_eof(s)

    ok, err = try_parse(s, str(rel))
    if ok:
        out.write_text(s, encoding="utf-8"); meta["result"] = "parsed_after_repairs"; return meta

    if isinstance(err, SyntaxError) and "unterminated string literal" in str(err).lower() and err.lineno:
        s3, changed = fix_unterminated_single_line(s, err.lineno)
        if changed:
            meta["actions"].append(f"closed single-line quote at line {err.lineno}")
            ok2, err2 = try_parse(s3, str(rel))
            if ok2:
                out.write_text(s3, encoding="utf-8"); meta["result"] = "parsed_after_targeted_fix"; return meta
            s, err = s3, err2

    if comment_on_fail and isinstance(err, SyntaxError) and err.lineno:
        s4 = comment_out_line(s, err.lineno, reason=str(err))
        ok3, _ = try_parse(s4, str(rel))
        if ok3:
            out.write_text(s4, encoding="utf-8"); meta["actions"].append(f"commented line {err.lineno}")
            meta["result"] = "parsed_after_comment"; return meta

    # still failing -> copy original into mirror to keep structure; mark error
    out.write_text(raw, encoding="utf-8")
    meta["result"] = "still_fails"
    meta["error"]  = {"msg": str(err), "lineno": getattr(err, "lineno", None), "offset": getattr(err, "offset", None)}
    return meta

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--comment-on-fail", action="store_true",
                    help="If parse still fails, comment only the failing line (preserved).")
    ap.add_argument("--only", nargs="*", help="Limit to these glob patterns (relative paths).")
    args = ap.parse_args()

    results = []
    files = []
    for p in ROOT.rglob("*.py"):
        rel = str(p.relative_to(ROOT)).replace("\\","/")
        if rel.endswith(".failed.py") or ignored(rel):
            continue
        if args.only and not any(fnmatch.fnmatch(rel, pat) for pat in args.only):
            continue
        files.append(p)

    for i, p in enumerate(sorted(files, key=lambda x: str(x))):
        meta = process_file(p, comment_on_fail=args.comment_on_fail)
        results.append(meta)
        print(f"[{i+1}/{len(files)}] {meta['file']}: {meta['result']}")

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "manifest.json").write_text(json.dumps({"files": results}, indent=2), encoding="utf-8")

    from collections import Counter
    c = Counter(m["result"] for m in results)
    print("\nSummary:", dict(c))
    print(f"📦 Manifest: {OUT/'manifest.json'}")

if __name__ == "__main__":
    main()
