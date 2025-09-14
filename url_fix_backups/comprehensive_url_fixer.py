#!/usr/bin/env python3
"""
COMPREHENSIVE URL SPACE FIXER
Fixes all URLs and API endpoints with spaces around slashes across the entire codebase.
Handles massive volumes efficiently with proper encoding and backup support.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Set
import shutil

# File extensions to process
TARGET_EXTENSIONS = {
    ".py",
    ".js",
    ".html",
    ".css",
    ".json",
    ".md",
    ".txt",
    ".sh",
    ".yml",
    ".yaml",
    ".xml",
    ".conf",
    ".cfg",
    ".ini",
}

# Directories to skip
SKIP_DIRS = {
    "venv",
    "venv_creative",
    ".venv",
    "env",
    ".env",
    "node_modules",
    "__pycache__",
    ".git",
    ".pytest_cache",
    "build",
    "dist",
    ".tox",
    "site-packages",
    ".mypy_cache",
    "htmlcov",
    ".coverage",
    "eggs",
    "*.egg-info",
    "backups",
}


class ComprehensiveURLFixer:
    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir).resolve()
        self.files_processed = 0
        self.files_fixed = 0
        self.total_fixes = 0
        self.backup_dir = self.root_dir / "url_fix_backups"

    def should_skip_path(self, path: Path) -> bool:
        """Check if we should skip this path."""
        path_parts = path.parts

        # Skip if any part of path matches skip dirs
        for part in path_parts:
            if part in SKIP_DIRS or (part.startswith(".") and part != "."):
                return True

        # Only process target file extensions
        if path.suffix not in TARGET_EXTENSIONS:
            return True

        return False

    def create_backup(self, file_path: Path) -> bool:
        """Create backup of file before modification."""
        try:
            if not self.backup_dir.exists():
                self.backup_dir.mkdir(parents=True, exist_ok=True)

            # Create relative path structure in backup
            rel_path = file_path.relative_to(self.root_dir)
            backup_path = self.backup_dir / rel_path
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(file_path, backup_path)
            return True
        except Exception as e:
            print(f"⚠️  Could not create backup for {file_path}: {e}")
            return False

    def read_file_safe(self, file_path: Path) -> tuple[str, str]:
        """Safely read file with multiple encoding attempts."""
        encodings = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]

        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    content = f.read()
                return content, encoding
            except UnicodeDecodeError:
                continue

        raise UnicodeDecodeError(f"Could not decode {file_path} with any encoding")

    def fix_url_spaces(self, content: str) -> tuple[str, int]:
        """Fix all URL and API endpoint spaces."""
        fixes_count = 0

        # Comprehensive URL space patterns
        patterns = [
            # HTTP/HTTPS URLs with spaces
            (r'(https?://)([^\s"\'>]+)\s+/\s*([^\s"\'>]*)', r"\1\2/\3"),
            (r'(https?://[^\s"\'>]+)/\s+([^\s"\'>]*)', r"\1/\2"),
            # API endpoints with spaces
            (r'(["\'])/\s+api\s+/\s*([^"\'>]*)', r"\1/api/\2"),
            (r'(["\'])/\s*api\s+/\s+([^"\'>]*)', r"\1/api/\2"),
            (r'(["\'])/api\s+/\s*([^"\'>]*)', r"\1/api/\2"),
            # Health check endpoints
            (r'(["\'])/\s+health\s*(["\'>])', r"\1/health\2"),
            (r'(["\'])/health\s+(["\'>])', r"\1/health\2"),
            # Status endpoints
            (r'(["\'])/\s+status\s*(["\'>])', r"\1/status\2"),
            (r'(["\'])/status\s+(["\'>])', r"\1/status\2"),
            # Avatar endpoints
            (r'(["\'])/\s+avatar\s*/\s*([^"\'>]*)', r"\1/avatar/\2"),
            (r'(["\'])/avatar\s+/\s*([^"\'>]*)', r"\1/avatar/\2"),
            # General path patterns with spaces
            (r'(["\'])/\s+([a-zA-Z0-9_-]+)\s*/\s*([^"\'>]*)', r"\1/\2/\3"),
            (r'(["\'])/([a-zA-Z0-9_-]+)\s+/\s*([^"\'>]*)', r"\1/\2/\3"),
            # Route patterns
            (r'@app\.route\(["\']\s*/\s*([^"\'>]*)', r'@app.route("/\1'),
            (r'@router\.\w+\(["\']\s*/\s*([^"\'>]*)', r"@router.\g<0>"),
            # Fetch/request URLs
            (r'fetch\(["\']\s*/\s*([^"\'>]*)', r'fetch("/\1'),
            (r'axios\.[a-z]+\(["\']\s*/\s*([^"\'>]*)', r"axios.\g<0>"),
            # Template/static file paths
            (r'src=["\']\s*/\s*([^"\'>]*)', r'src="/\1'),
            (r'href=["\']\s*/\s*([^"\'>]*)', r'href="/\1'),
            # Configuration URLs
            (r'url\s*=\s*["\']\s*/\s*([^"\'>]*)', r'url="/\1'),
            (r'endpoint\s*=\s*["\']\s*/\s*([^"\'>]*)', r'endpoint="/\1'),
            # Generic slash space fixes
            (r"/\s+/", r"//"),
            (r"\s+/", r"/"),
            (r"/\s+", r"/"),
        ]

        original_content = content

        for pattern, replacement in patterns:
            new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            if new_content != content:
                fixes_count += len(re.findall(pattern, content, flags=re.MULTILINE))
                content = new_content

        return content, fixes_count

    def fix_file(self, file_path: Path) -> bool:
        """Fix a single file."""
        try:
            # Read file
            original_content, encoding = self.read_file_safe(file_path)

            # Apply URL fixes
            fixed_content, fixes_count = self.fix_url_spaces(original_content)

            # Only write if changes were made
            if fixed_content != original_content and fixes_count > 0:
                # Create backup first
                if not self.create_backup(file_path):
                    print(f"⚠️  Skipping {file_path} - backup failed")
                    return False

                # Write fixed content
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(fixed_content)

                self.files_fixed += 1
                self.total_fixes += fixes_count
                print(f"✅ Fixed {file_path.relative_to(self.root_dir)} ({fixes_count} fixes)")
                return True
            else:
                return False

        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return False

    def find_target_files(self) -> List[Path]:
        """Find all files to process."""
        target_files = []

        for root, dirs, files in os.walk(self.root_dir):
            # Remove skip directories from dirs list
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]

            for file in files:
                file_path = Path(root) / file
                if not self.should_skip_path(file_path):
                    target_files.append(file_path)

        return sorted(target_files)

    def run(self):
        """Run the comprehensive URL fixer."""
        print("🚀 COMPREHENSIVE URL SPACE FIXER")
        print("=" * 50)

        # Find files
        target_files = self.find_target_files()
        print(f"📁 Found {len(target_files)} files to process")

        if not target_files:
            print("❌ No files found to process!")
            return

        # Process files
        print("\n🔧 Processing files...")
        for file_path in target_files:
            self.fix_file(file_path)
            self.files_processed += 1

            # Progress indicator
            if self.files_processed % 100 == 0:
                print(f"📊 Progress: {self.files_processed}/{len(target_files)} files processed")

        # Summary
        print("\n" + "=" * 50)
        print("🎉 URL FIXING COMPLETE!")
        print(f"📊 Files processed: {self.files_processed}")
        print(f"🔧 Files fixed: {self.files_fixed}")
        print(f"✨ Total URL fixes applied: {self.total_fixes}")
        print(f"💾 Backups stored in: {self.backup_dir}")

        if self.files_fixed > 0:
            print("\n🎯 All URL spaces have been fixed!")
            print("💡 Run a grep search to verify remaining issues")
        else:
            print("\n✨ No URL space issues found!")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Comprehensive URL space fixer")
    parser.add_argument("--dir", default=".", help="Directory to process (default: current)")
    args = parser.parse_args()

    fixer = ComprehensiveURLFixer(args.dir)
    fixer.run()


if __name__ == "__main__":
    main()
