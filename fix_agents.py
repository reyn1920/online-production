#!/usr/bin/env python3
import json
import os
import re
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(os.getcwd())
DEFAULT_DB = Path("data/right_perspective.db")  # change with --db if needed


def ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def backup_file(path: Path):
    if not path.exists():
        return None
    bak = path.with_suffix(path.suffix + f".bak.{ts()}")
    shutil.copy2(path, bak)
    return bak


def find_files(patterns, exts=(".py",), max_files=50):
    matches = []
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix in exts:
            try:
                txt = p.read_text(encoding="utf-8", errors="ignore")
                if any(pat in txt for pat in patterns):
                    matches.append((p, txt))
            except Exception:
                continue
        if len(matches) >= max_files:
            break
    return matches


def patch_right_perspective_firewall():
    print("🔧 Patching RightPerspectiveFirewall...")
    candidates = find_files(["class RightPerspectiveFirewall"])
    if not candidates:
        print("  ⚠️ Could not find RightPerspectiveFirewall class in repo. Skipping.")
        return {"patched": False, "reason": "not_found"}

    patched_any = False
    details = []
    for path, txt in candidates:
        # Ensure __init__ exists and _rule_cache is set
        class_match = re.search(
            r"class\s+RightPerspectiveFirewall\s*(?:\([^)]*\))?\s*:\s*(?:\n\s+\"\"\".*?\"\"\"\s*)?",
            txt,
            re.S,
        )
        if not class_match:
            class_match = re.search(r"class\s+RightPerspectiveFirewall\s*:\s*", txt)
        if not class_match:
            continue

        if "_rule_cache" in txt:
            details.append(
                {"file": str(path), "patched": False, "reason": "cache_already_present"}
            )
            continue

        # Try to detect class block start and insert __init__ if missing
        has_init = re.search(r"def\s+__init__\s*\(", txt) is not None

        if has_init:
            # Inject self._rule_cache = {} at start of __init__ if missing
            init_match = re.search(
                r"(def\s+__init__\s*\([^)]*\)\s*:)(.*?)(?=\n\s*def|\n\s*class|\Z)",
                txt,
                re.S,
            )
            if init_match:
                init_body = init_match.group(2)
                if "self._rule_cache" not in init_body:
                    # Find first line after __init__ declaration to insert cache initialization
                    lines = txt.split("\n")
                    new_lines = []
                    in_init = False
                    init_indent = None
                    cache_added = False

                    for line in lines:
                        new_lines.append(line)
                        if re.match(r"\s*def\s+__init__\s*\(", line):
                            in_init = True
                            init_indent = len(line) - len(line.lstrip())
                        elif in_init and not cache_added:
                            # Look for first non-empty line in __init__ body
                            if (
                                line.strip()
                                and not line.strip().startswith('"""')
                                and not line.strip().startswith("'''")
                            ):
                                # Add cache initialization before this line
                                cache_line = (
                                    " " * (init_indent + 4) + "self._rule_cache = {}"
                                )
                                new_lines.insert(-1, cache_line)
                                cache_added = True
                                in_init = False

                    if cache_added:
                        backup_file(path)
                        path.write_text("\n".join(new_lines), encoding="utf-8")
                        patched_any = True
                        details.append(
                            {
                                "file": str(path),
                                "patched": True,
                                "reason": "added_cache_to_init",
                            }
                        )
                    else:
                        details.append(
                            {
                                "file": str(path),
                                "patched": False,
                                "reason": "could_not_locate_init_body",
                            }
                        )
                else:
                    details.append(
                        {
                            "file": str(path),
                            "patched": False,
                            "reason": "cache_already_in_init",
                        }
                    )
        else:
            # Add __init__ method with _rule_cache
            class_start = class_match.end()
            # Find the indentation level
            class_line = txt[:class_start].split("\n")[-1]
            base_indent = len(class_line) - len(class_line.lstrip())
            method_indent = " " * (base_indent + 4)
            body_indent = " " * (base_indent + 8)

            init_method = f"\n{method_indent}def __init__(self):\n{body_indent}self._rule_cache = {{}}\n"

            new_txt = txt[:class_start] + init_method + txt[class_start:]
            backup_file(path)
            path.write_text(new_txt, encoding="utf-8")
            patched_any = True
            details.append(
                {"file": str(path), "patched": True, "reason": "added_init_with_cache"}
            )

    return {"patched": patched_any, "details": details}


def patch_content_agent():
    print("🔧 Patching ContentAgent shutil import...")
    candidates = find_files(["class ContentAgent", "shutil."])
    if not candidates:
        print("  ⚠️ Could not find ContentAgent class or shutil usage. Skipping.")
        return {"patched": False, "reason": "not_found"}

    patched_any = False
    details = []

    for path, txt in candidates:
        if "class ContentAgent" not in txt:
            continue

        # Check if shutil is used but not imported
        has_shutil_usage = "shutil." in txt
        has_shutil_import = re.search(
            r"^\s*import\s+shutil\s*$|^\s*from\s+\S+\s+import\s+.*shutil", txt, re.M
        )

        if has_shutil_usage and not has_shutil_import:
            # Add shutil import
            lines = txt.split("\n")
            import_inserted = False

            # Find the best place to insert import (after other imports)
            for i, line in enumerate(lines):
                if line.strip().startswith("import ") or line.strip().startswith(
                    "from "
                ):
                    continue
                elif (
                    line.strip() == ""
                    and i > 0
                    and (
                        lines[i - 1].strip().startswith("import ")
                        or lines[i - 1].strip().startswith("from ")
                    )
                ):
                    # Insert after import block
                    lines.insert(i, "import shutil")
                    import_inserted = True
                    break
                elif not line.strip().startswith("#") and line.strip() != "":
                    # Insert before first non-import, non-comment line
                    lines.insert(i, "import shutil")
                    import_inserted = True
                    break

            if not import_inserted:
                # Fallback: insert at the beginning after shebang/encoding
                insert_pos = 0
                for i, line in enumerate(lines[:5]):
                    if line.startswith("#!"):
                        insert_pos = i + 1
                    elif "coding:" in line or "encoding:" in line:
                        insert_pos = i + 1
                lines.insert(insert_pos, "import shutil")

            backup_file(path)
            path.write_text("\n".join(lines), encoding="utf-8")
            patched_any = True
            details.append(
                {"file": str(path), "patched": True, "reason": "added_shutil_import"}
            )
        else:
            reason = (
                "no_shutil_usage" if not has_shutil_usage else "import_already_present"
            )
            details.append({"file": str(path), "patched": False, "reason": reason})

    return {"patched": patched_any, "details": details}


def patch_database(db_path: Path):
    print(f"🔧 Patching database schema at {db_path}...")
    if not db_path.exists():
        print(f"  ⚠️ Database not found at {db_path}. Skipping.")
        return {"patched": False, "reason": "db_not_found"}

    # Backup database
    backup_file(db_path)

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if api_discovery_tasks table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='api_discovery_tasks';"
        )
        table_exists = cursor.fetchone() is not None

        if table_exists:
            # Check current schema
            cursor.execute("PRAGMA table_info(api_discovery_tasks);")
            columns = cursor.fetchall()

            # Check if task_type has NOT NULL constraint
            task_type_col = None
            for col in columns:
                if col[1] == "task_type":
                    task_type_col = col
                    break

            if task_type_col and task_type_col[3] == 1:  # NOT NULL constraint exists
                print(
                    "  📝 Recreating api_discovery_tasks table to remove NOT NULL constraint..."
                )

                # Get existing data
                cursor.execute("SELECT * FROM api_discovery_tasks;")
                existing_data = cursor.fetchall()

                # Drop and recreate table
                cursor.execute("DROP TABLE api_discovery_tasks;")
                cursor.execute(
                    """
                    CREATE TABLE api_discovery_tasks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_type TEXT DEFAULT 'general',
                        status TEXT DEFAULT 'pending',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        data TEXT
                    );
                """
                )

                # Restore data with proper column mapping
                if existing_data:
                    # Map old data to new schema (6 columns: id, task_type, status, created_at, updated_at, data)
                    for row in existing_data:
                        # Handle different row lengths gracefully
                        if len(row) >= 6:
                            cursor.execute(
                                "INSERT INTO api_discovery_tasks (id, task_type, status, created_at, updated_at, data) VALUES (?, ?, ?, ?, ?, ?);",
                                row[:6],
                            )
                        else:
                            # Pad with defaults if row is shorter
                            padded_row = list(row) + [None] * (6 - len(row))
                            cursor.execute(
                                "INSERT INTO api_discovery_tasks (id, task_type, status, created_at, updated_at, data) VALUES (?, ?, ?, ?, ?, ?);",
                                padded_row[:6],
                            )

                conn.commit()
                conn.close()
                return {"patched": True, "reason": "recreated_table"}
            else:
                conn.close()
                return {"patched": False, "reason": "no_not_null_constraint"}
        else:
            # Create table with correct schema
            cursor.execute(
                """
                CREATE TABLE api_discovery_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_type TEXT DEFAULT 'general',
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data TEXT
                );
            """
            )
            conn.commit()
            conn.close()
            return {"patched": True, "reason": "created_table"}

    except Exception as e:
        print(f"  ❌ Database patch failed: {e}")
        return {"patched": False, "reason": f"error: {e}"}


def main():
    print("🚀 Starting agent fixes...")

    # Parse command line args
    db_path = DEFAULT_DB
    if "--db" in sys.argv:
        idx = sys.argv.index("--db")
        if idx + 1 < len(sys.argv):
            db_path = Path(sys.argv[idx + 1])

    results = {}

    # Fix 1: Database schema
    results["database"] = patch_database(db_path)

    # Fix 2: ContentAgent shutil import
    results["content_agent"] = patch_content_agent()

    # Fix 3: RightPerspectiveFirewall _rule_cache
    results["firewall"] = patch_right_perspective_firewall()

    # Summary
    print("\n📊 Fix Summary:")
    for component, result in results.items():
        status = "✅ FIXED" if result.get("patched", False) else "⚠️ SKIPPED"
        reason = result.get("reason", "unknown")
        print(f"  {component}: {status} ({reason})")
        if "details" in result:
            for detail in result["details"]:
                file_status = "✅" if detail.get("patched", False) else "⚠️"
                detail_reason = detail.get("reason", "unknown")
                print(f"    {file_status} {detail['file']}: {detail_reason}")

    print("\n🎉 Agent fixes completed!")
    return results


if __name__ == "__main__":
    main()
