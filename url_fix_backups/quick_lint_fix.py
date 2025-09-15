#!/usr / bin / env python3
""""""
Quick lint fix for deployment readiness
Fixes specific issues preventing git commit
""""""

import os
import re
from pathlib import Path


def fix_trailing_whitespace(file_path):
    """Remove trailing whitespace from file"""
    try:
        with open(file_path, "r", encoding="utf - 8") as f:
            content = f.read()

        # Remove trailing whitespace from each line
        lines = content.splitlines()
        fixed_lines = [line.rstrip() for line in lines]

        with open(file_path, "w", encoding="utf - 8") as f:
            f.write("\\n".join(fixed_lines))
            if content.endswith("\\n"):
                f.write("\\n")

        print(f"✅ Fixed trailing whitespace in {file_path}")
        return True
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False


def fix_bare_except(file_path):
    """Fix bare except clauses"""
    try:
        with open(file_path, "r", encoding="utf - 8") as f:
            content = f.read()

        # Replace bare except with except Exception
        content = re.sub(
            r"except Exception:\\s*$", "except Exception:", content, flags=re.MULTILINE
# BRACKET_SURGEON: disabled
#         )

        with open(file_path, "w", encoding="utf - 8") as f:
            f.write(content)

        print(f"✅ Fixed bare except in {file_path}")
        return True
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False


def fix_blank_line_whitespace(file_path):
    """Fix blank lines containing whitespace"""
    try:
        with open(file_path, "r", encoding="utf - 8") as f:
            content = f.read()

        # Replace blank lines with whitespace with truly blank lines
        content = re.sub(r"^\\s+$", "", content, flags=re.MULTILINE)

        with open(file_path, "w", encoding="utf - 8") as f:
            f.write(content)

        print(f"✅ Fixed blank line whitespace in {file_path}")
        return True
    except Exception as e:
        print(f"❌ Error fixing {file_path}: {e}")
        return False


def main():
    """Fix specific linting issues in main project files"""
    print("🔧 Quick Lint Fix - Targeting specific issues...")

    # Files with specific issues from the commit log
    problem_files = [
        "utils / rule1_scanner.py",
        "verify_cloud_software_integration.py",
        "view_affiliate_credentials.py",
# BRACKET_SURGEON: disabled
#     ]

    project_root = Path.cwd()
    fixed_count = 0

    for file_path in problem_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"\\n🔍 Processing {file_path}...")

            # Fix trailing whitespace and blank line whitespace
            if fix_trailing_whitespace(full_path):
                fixed_count += 1

            # Fix blank line whitespace
            if fix_blank_line_whitespace(full_path):
                pass  # Already counted above

            # Fix bare except clauses
            if fix_bare_except(full_path):
                pass  # Already counted above
        else:
            print(f"⚠️  File not found: {file_path}")

    print(f"\\n✅ Quick lint fix completed! Fixed {fixed_count} files.")
    print("🚀 Ready to retry git commit.")


if __name__ == "__main__":
    main()