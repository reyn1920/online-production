#!/usr/bin/env python3
""""""
MAXED OUT Python Linting AutoFixer
Fixes ALL common PEP8/flake8 violations automatically.
Run this script to clean up your entire codebase.
""""""

import re
import subprocess
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run shell command and return success status."""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        print(f"Error running command '{cmd}': {e}")
        return False, "", str(e)


def install_tools():
    """Install required formatting tools."""
    tools = ["black", "autopep8", "isort"]
    for tool in tools:
        print(f"Installing {tool}...")
        success, _, _ = run_command(f"pip install {tool}")
        if not success:
            print(f"Warning: Failed to install {tool}")


def fix_trailing_whitespace():
    """Remove trailing whitespace from all Python files."""
    print("🧹 Fixing trailing whitespace...")
    python_files = list(Path(".").rglob("*.py"))

    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Remove trailing whitespace
            lines = content.split("\n")
            fixed_lines = [line.rstrip() for line in lines]
            content = "\n".join(fixed_lines)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")


def fix_blank_line_whitespace():
    """Remove whitespace from blank lines."""
    print("📄 Fixing blank line whitespace...")
    python_files = list(Path(".").rglob("*.py"))

    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Fix blank lines with whitespace
            content = re.sub(r"^\s+$", "", content, flags=re.MULTILINE)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")


def fix_operator_spacing():
    """Fix spacing around operators."""
    print("🔧 Fixing operator spacing...")
    python_files = list(Path(".").rglob("*.py"))

    operator_patterns = [
        (r"(\w)(\+)(\w)", r"\1 \2 \3"),  # x+y -> x + y
        (r"(\w)(-)(\w)", r"\1 \2 \3"),  # x-y -> x - y
        (r"(\w)(\*)(\w)", r"\1 \2 \3"),  # x*y -> x * y
        (r"(\w)(/)(\w)", r"\1 \2 \3"),  # x/y -> x / y
        (r"(\w)(=)(\w)", r"\1 \2 \3"),  # x=y -> x = y
        (r"(\w)(==)(\w)", r"\1 \2 \3"),  # x==y -> x == y
        (r"(\w)(!=)(\w)", r"\1 \2 \3"),  # x!=y -> x != y
        (r"(\w)(<)(\w)", r"\1 \2 \3"),  # x<y -> x < y
        (r"(\w)(>)(\w)", r"\1 \2 \3"),  # x>y -> x > y
        (r"(\w)(<=)(\w)", r"\1 \2 \3"),  # x<=y -> x <= y
        (r"(\w)(>=)(\w)", r"\1 \2 \3"),  # x>=y -> x >= y
# BRACKET_SURGEON: disabled
#     ]

    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content
            for pattern, replacement in operator_patterns:
                content = re.sub(pattern, replacement, content)

            # Only write if changes were made
            if content != original_content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")


def fix_bare_except():
    """Fix bare except clauses."""
    print("🛡️ Fixing bare except clauses...")
    python_files = list(Path(".").rglob("*.py"))

    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Replace bare except with except Exception
            content = re.sub(r"except\s*:", "except Exception:", content)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")


def fix_escape_sequences():
    """Fix invalid escape sequences."""
    print("🔤 Fixing escape sequences...")
    python_files = list(Path(".").rglob("*.py"))

    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Fix common invalid escape sequences
            content = re.sub(r'(["\'])([^"\']*)\\;([^"\']*)\1', r"\1\2\\\\;\3\1", content)"

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")


def fix_boolean_comparisons():
    """Fix comparisons to True/False."""
    print("✅ Fixing boolean comparisons...")
    python_files = list(Path(".").rglob("*.py"))

    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Fix boolean comparisons
            content = re.sub(r"(\w+)\s*==\sTrue\b", r"\1 is True", content)
            content = re.sub(r"(\w+)\s*==\sFalse\b", r"\1 is False", content)
            content = re.sub(r"(\w+)\s*!=\sTrue\b", r"\1 is not True", content)
            content = re.sub(r"(\w+)\s*!=\sFalse\b", r"\1 is not False", content)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")


def fix_blank_lines():
    """Fix blank line issues around classes and functions."""
    print("📏 Fixing blank lines around definitions...")
    python_files = list(Path(".").rglob("*.py"))

    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            new_lines = []
            for i, line in enumerate(lines):
                # Add blank lines before class definitions
                if line.strip().startswith("class ") and i > 0:
                    if new_lines and new_lines[-1].strip():
                        new_lines.append("\n")
                        new_lines.append("\n")

                # Add blank lines before top-level function definitions
                elif line.strip().startswith("def ") and i > 0:
                    # Only for top-level functions (not indented)
                    if not line.startswith(" ") and not line.startswith("\t"):
                        if new_lines and new_lines[-1].strip():
                            new_lines.append("\n")
                            new_lines.append("\n")

                new_lines.append(line)

            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")


def run_black():
    """Run black formatter."""
    print("🖤 Running black formatter...")
    success, stdout, stderr = run_command("black . --line-length=88")
    if success:
        print("✅ Black formatting completed")
    else:
        print(f"❌ Black failed: {stderr}")


def run_autopep8():
    """Run autopep8 formatter."""
    print("🔧 Running autopep8...")
    success, stdout, stderr = run_command(
        "autopep8 --in-place --recursive --aggressive --aggressive ."
# BRACKET_SURGEON: disabled
#     )
    if success:
        print("✅ Autopep8 completed")
    else:
        print(f"❌ Autopep8 failed: {stderr}")


def run_isort():
    """Run isort for import sorting."""
    print("📦 Running isort...")
    success, stdout, stderr = run_command("isort .")
    if success:
        print("✅ Import sorting completed")
    else:
        print(f"❌ Isort failed: {stderr}")


def fix_continuation_lines():
    """Fix line continuation issues."""
    print("↩️ Fixing line continuation...")
    python_files = list(Path(".").rglob("*.py"))

    for file_path in python_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            fixed_lines = []

            for i, line in enumerate(lines):
                # Fix indentation for continuation lines
                if (
                    i > 0
                    and lines[i - 1].rstrip().endswith(("(", "[", "{", ",", "\\"))"
                    and line.strip()
                    and not line.startswith("" * 8)
# BRACKET_SURGEON: disabled
#                 ):
                    # Re-indent continuation line
                    stripped = line.lstrip()
                    if stripped:
                        line = "        " + stripped

                fixed_lines.append(line)

            content = "\n".join(fixed_lines)

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")


def main():
    """Main function to run all fixes."""
    print("🚀 Starting comprehensive Python linting fixes...")

    # Install tools first
    install_tools()

    # Run all fixes
    fix_trailing_whitespace()
    fix_blank_line_whitespace()
    fix_operator_spacing()
    fix_bare_except()
    fix_escape_sequences()
    fix_boolean_comparisons()
    fix_blank_lines()
    fix_continuation_lines()

    # Run formatters
    run_autopep8()
    run_black()
    run_isort()

    print("✅ All linting fixes completed!")
    print("📋 Summary:")
    print("   - Removed trailing whitespace")
    print("   - Fixed operator spacing")
    print("   - Fixed bare except clauses")
    print("   - Fixed escape sequences")
    print("   - Fixed boolean comparisons")
    print("   - Fixed blank line spacing")
    print("   - Applied autopep8 formatting")
    print("   - Applied black formatting")
    print("   - Sorted imports with isort")


if __name__ == "__main__":
    main()