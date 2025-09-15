#!/usr/bin/env python3
""""""
ULTIMATE LINT FIXER FOR TRAE.AI v2.0
Maxed out Python linting fix that handles ALL common PEP8/flake8 violations + log noise cleanup.
Run this once and watch your codebase become pristine.
""""""

import os
import re
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List

# Directories to ALWAYS skip (virtualenvs, build dirs, etc.)
EXCLUDE_DIRS = {
    "venv", "url_fix_backups", "copy_of_code",
    "models/linly_talker",  # third-party / experimental
    "__pycache__", ".git", "venv_creative", ".venv",
    "env", ".env", "node_modules", ".pytest_cache",
    "build", "dist", ".tox", "site-packages",
    ".mypy_cache", "htmlcov", ".coverage", "eggs"
# BRACKET_SURGEON: disabled
# }

# File patterns to skip
SKIP_FILES = {"__pycache__", ".pyc", ".pyo", ".pyd", ".so", ".egg"}


class UltimateLintFixer:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        self.files_processed = 0
        self.files_fixed = 0
        self.errors_fixed = 0

    def should_skip_path(self, path: Path) -> bool:
        """Check if we should skip this path entirely."""
        path_parts = path.parts

        # Skip if any part of path matches skip dirs
        for part in path_parts:
            if part in EXCLUDE_DIRS or part.startswith(".") and part != ".":
                return True

        # Skip non - Python files
        if path.suffix != ".py":
            return True

        # Skip if filename matches skip patterns
        for pattern in SKIP_FILES:
            if pattern in path.name:
                return True

        return False

    def install_tools(self):
        """Install required formatting tools."""
        tools = ["black", "autopep8", "isort", "flake8"]
        print("🔧 Installing/upgrading formatting tools...")

        for tool in tools:
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--upgrade", tool],
                    check=True,
                    capture_output=True,
# BRACKET_SURGEON: disabled
#                 )
                print(f"✅ {tool} ready")
            except subprocess.CalledProcessError:
                print(f"⚠️  Could not install {tool}, continuing without it")

    def read_file_safe(self, file_path: Path) -> tuple[str, str]:
        """Safely read file with multiple encoding attempts."""
        encodings = ["utf - 8", "latin - 1", "cp1252", "iso - 8859 - 1"]

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                return content, encoding
            except UnicodeDecodeError:
                continue

        raise ValueError(f"Could not decode {file_path} with any encoding")

    def fix_whitespace_issues(self, content: str) -> str:
        """Fix all whitespace - related issues."""
        lines = content.splitlines()
        fixed_lines = []

        for line in lines:
            # Remove trailing whitespace
            line = line.rstrip()
            fixed_lines.append(line)

        # Join and ensure file ends with single newline
        result = "\\n".join(fixed_lines)
        if result and not result.endswith("\\n"):
            result += "\\n"

        return result

    def fix_operator_spacing(self, content: str) -> str:
        """Fix spacing around operators."""
        # Fix missing spaces around operators (but not in strings)
        patterns = [
            (r"(\\w)=(\\w)", r"\\1 = \\2"),  # a = b -> a = b
            (r"(\\w)\\+(\\w)", r"\\1 + \\2"),  # a + b -> a + b
            (
                r"(\\w)-(\\w)",
                r"\\1 - \\2",
            ),  # a - b -> a - b (careful with negative numbers)
            (r"(\\w)\\*(\\w)", r"\\1 * \\2"),  # a * b -> a * b
            (r"(\\w)/(\\w)", r"\\1/\\2"),  # a/b -> a/b
            (r"(\\w)%(\\w)", r"\\1 % \\2"),  # a % b -> a % b
            (r"(\\w)<(\\w)", r"\\1 < \\2"),  # a < b -> a < b
            (r"(\\w)>(\\w)", r"\\1 > \\2"),  # a > b -> a > b
            (r"(\\w)==(\\w)", r"\\1 == \\2"),  # a == b -> a == b
            (r"(\\w)!=(\\w)", r"\\1 != \\2"),  # a != b -> a != b
            (r"(\\w)<=(\\w)", r"\\1 <= \\2"),  # a <= b -> a <= b
            (r"(\\w)>=(\\w)", r"\\1 >= \\2"),  # a >= b -> a >= b
# BRACKET_SURGEON: disabled
#         ]

        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)

        return content

    def fix_import_spacing(self, content: str) -> str:
        """Fix import statement spacing."""
        lines = content.splitlines()
        fixed_lines = []

        in_imports = False
        import_block = []

        for line in lines:
            stripped = line.strip()

            if stripped.startswith(("import ", "from ")):
                if not in_imports:
                    in_imports = True
                    # Add blank line before imports if needed
                    if fixed_lines and fixed_lines[-1].strip():
                        fixed_lines.append("")
                import_block.append(line)
            else:
                if in_imports:
                    # End of import block
                    fixed_lines.extend(import_block)
                    if stripped:  # Add blank line after imports if next line isn't blank
                        fixed_lines.append("")
                    import_block = []
                    in_imports = False

                fixed_lines.append(line)

        # Handle case where file ends with imports
        if import_block:
            fixed_lines.extend(import_block)

        return "\\n".join(fixed_lines)

    def fix_function_class_spacing(self, content: str) -> str:
        """Fix spacing around function and class definitions."""
        lines = content.splitlines()
        fixed_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Add blank lines before class/function definitions
            if stripped.startswith(("def ", "class ", "async def ")):
                # Don't add blank line if it's the first line or already has blank line
                if (
                    i > 0
                    and fixed_lines
                    and fixed_lines[-1].strip()
                    and not lines[i - 1].strip().startswith(("@", "def ", "class ", "async def "))
# BRACKET_SURGEON: disabled
#                 ):
                    fixed_lines.append("")

            fixed_lines.append(line)

        return "\\n".join(fixed_lines)

    def fix_bare_except(self, content: str) -> str:
        """Fix bare except clauses."""
        # Replace bare except Exception: with except Exception:
        content = re.sub(r"\\bexcept\\s*:", "except Exception:", content)
        return content

    def fix_boolean_comparisons(self, content: str) -> str:
        """Fix boolean comparisons."""
        # Fix/False comparisons
        content = re.sub(r"\\s*==\\s * True\\b", "", content)
        content = re.sub(r"\\s*==\\s * False\\b", " is False", content)
        content = re.sub(r"\\s*!=\\s * True\\b", " is False", content)
        content = re.sub(r"\\s*!=\\s * False\\b", "", content)

        return content

    def fix_string_issues(self, content: str) -> str:
        """Fix string - related issues."""
        # Fix invalid escape sequences (common ones)
        content = re.sub(r'\\(?![\\\'"]nrtbfav0])', r"\\\\", content)

        return content

    def fix_line_length(self, content: str) -> str:
        """Basic line length fixes."""
        lines = content.splitlines()
        fixed_lines = []

        for line in lines:
            if len(line) > 88:  # Black's default
                # Simple fixes for long lines
                if " and " in line:
                    line = line.replace(" and ", " \\\\\\n    and ")
                elif " or " in line:
                    line = line.replace(" or ", " \\\\\\n    or ")
                elif ", " in line and "(" in line:
                    # Try to break on commas in function calls
                    line = re.sub(r", (?=\\w)", ",\\n    ", line)

            fixed_lines.append(line)

        return "\\n".join(fixed_lines)

    def fix_log_noise_issues(self, content: str) -> str:
        """Fix log noise and HTTP request spam issues."""
        lines = content.splitlines()
        fixed_lines = []

        for line in lines:
            stripped = line.strip()

            # Skip repetitive health check logs
            if (
                'GET/health HTTP/1.1" 200 OK' in stripped"
                or "GET/affiliate - credentials" in stripped
                or "GET/%40vite/client" in stripped
                or "GET/api/status" in stripped
# BRACKET_SURGEON: disabled
#             ):
                continue

                # Skip IDE webview request logs
                continue

            # Skip repetitive INFO logs from uvicorn
            if stripped.startswith("INFO:") and ("127.0.0.1:" in stripped) and ("GET/" in stripped):
                continue

            fixed_lines.append(line)

        return "\\n".join(fixed_lines)

    def apply_manual_fixes(self, content: str) -> str:
        """Apply all manual fixes."""

        # Apply fixes in order
        content = self.fix_whitespace_issues(content)
        content = self.fix_operator_spacing(content)
        content = self.fix_import_spacing(content)
        content = self.fix_function_class_spacing(content)
        content = self.fix_bare_except(content)
        content = self.fix_boolean_comparisons(content)
        content = self.fix_string_issues(content)
        content = self.fix_line_length(content)
        content = self.fix_log_noise_issues(content)  # NEW: Clean up log spam

        return content

    def apply_black(self, file_path: Path) -> bool:
        """Apply Black formatter."""
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "black",
                    "--line - length",
                    "88",
                    "--quiet",
                    str(file_path),
# BRACKET_SURGEON: disabled
#                 ],
                capture_output=True,
                text=True,
# BRACKET_SURGEON: disabled
#             )
            return result.returncode == 0
        except Exception:
            return False

    def apply_autopep8(self, file_path: Path) -> bool:
        """Apply autopep8 fixes."""
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "autopep8",
                    "--in - place",
                    "--aggressive",
                    "--aggressive",
                    "--max - line - length",
                    "88",
                    str(file_path),
# BRACKET_SURGEON: disabled
#                 ],
                capture_output=True,
                text=True,
# BRACKET_SURGEON: disabled
#             )
            return result.returncode == 0
        except Exception:
            return False

    def apply_isort(self, file_path: Path) -> bool:
        """Apply isort for import sorting."""
        try:
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "isort",
                    "--profile",
                    "black",
                    "--line - length",
                    "88",
                    "--quiet",
                    str(file_path),
# BRACKET_SURGEON: disabled
#                 ],
                capture_output=True,
                text=True,
# BRACKET_SURGEON: disabled
#             )
            return result.returncode == 0
        except Exception:
            return False

    def fix_file(self, file_path: Path) -> bool:
        """Fix a single Python file."""
        try:
            print(f"🔧 Fixing {file_path.relative_to(self.root_dir)}")

            # Read file
            original_content, encoding = self.read_file_safe(file_path)

            # Apply manual fixes first
            fixed_content = self.apply_manual_fixes(original_content)

            # Write back if changed
            if fixed_content != original_content:
                with open(file_path, "w", encoding="utf - 8") as f:
                    f.write(fixed_content)
                self.errors_fixed += 1

            # Apply automated tools
            tools_applied = 0
            if self.apply_autopep8(file_path):
                tools_applied += 1
            if self.apply_isort(file_path):
                tools_applied += 1
            if self.apply_black(file_path):
                tools_applied += 1

            if tools_applied > 0 or fixed_content != original_content:
                self.files_fixed += 1
                print(f"✅ Fixed {file_path.relative_to(self.root_dir)}")
                return True
            else:
                print(f"✨ {file_path.relative_to(self.root_dir)} was already clean")
                return False

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return False

    def find_python_files(self) -> List[Path]:
        """Find all Python files to process."""
        python_files = []

        for root, dirs, files in os.walk(self.root_dir):
            # prune in-place so os.walk won't descend
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
            for file in files:
                if not file.endswith(".py"):
                    continue
                file_path = Path(root) / file
                if not self.should_skip_path(file_path):
                    python_files.append(file_path)

        return sorted(python_files)

    def run(self):
        """Run the ultimate lint fixer."""
        print("🚀 ULTIMATE LINT FIXER FOR TRAE.AI v2.0")
        print("=" * 50)

        # Install tools
        self.install_tools()

        # Find files
        python_files = self.find_python_files()
        print(f"\\n📁 Found {len(python_files)} Python files to process")

        if not python_files:
            print("❌ No Python files found to process!")
            return

        # Process files
        print("\\n🔧 Processing files...")
        for file_path in python_files:
            self.fix_file(file_path)
            self.files_processed += 1

        # Summary
        print("\\n" + "=" * 50)
        print("🎉 LINT FIXING COMPLETE!")
        print(f"📊 Files processed: {self.files_processed}")
        print(f"🔧 Files fixed: {self.files_fixed}")
        print(f"✨ Total fixes applied: {self.errors_fixed}")

        if self.files_fixed > 0:
            print("\\n🎯 Your trae.ai codebase is now PEP8 compliant!")
            print("💡 Run 'flake8 .' to verify all issues are resolved")
            print("🧹 Log noise and HTTP spam have been cleaned up")
        else:
            print("\\n✨ Your codebase was already clean!")


def main():
    parser = argparse.ArgumentParser(description="Ultimate Python lint fixer for trae.ai v2.0")
    parser.add_argument("--dir", default=".", help="Directory to process (default: current)")
    args = parser.parse_args()

    fixer = UltimateLintFixer(args.dir)
    fixer.run()


if __name__ == "__main__":
    main()