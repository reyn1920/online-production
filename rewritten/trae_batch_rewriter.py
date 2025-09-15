#!/usr/bin/env python3
""""""
Trae Batch Rewriter - Advanced syntax error repair using safe pre-fixes + LLM assistance

This script:
1. Applies safe "pre-fixes" (e.g., turn a - z → a-z, 2e - 1 → 2e-1)
2. If a file still doesn't parse, sends file + AST error to Trae.ai for rewriting'
3. Validates LLM output; retries once with new error if still broken
4. Backs up originals before writing; failed attempts save as .failed.py
""""""

import argparse
import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

# Skip directories
SKIP_DIRS = {
    'venv', 'venv_stable', 'venv_creative', '.venv', 'node_modules',
    '.git', '__pycache__', '.pytest_cache', '.ruff_cache', '.trae'
# BRACKET_SURGEON: disabled
# }

class TraeBatchRewriter:
    def __init__(self, llm_cmd: str = "trae chat --model code-repair --stdin"):
        self.llm_cmd = llm_cmd
        self.stats = {
            'processed': 0,
            'pre_fixed': 0,
            'llm_fixed': 0,
            'failed': 0,
            'skipped': 0
# BRACKET_SURGEON: disabled
#         }

    def apply_safe_prefixes(self, content: str) -> str:
        """Apply safe pre-fixes for common syntax errors."""
        original_content = content

        # Fix spaced character ranges in regex (a - z → a-z)
        content = re.sub(r'\[([^\]]*?)\s+-\s+([^\]]*?)\]', r'[\1-\2]', content)

        # Fix spaced scientific notation (2e - 1 → 2e-1)
        content = re.sub(r'(\d+e)\s*-\s*(\d+)', r'\1-\2', content, flags=re.IGNORECASE)
        content = re.sub(r'(\d+e)\s*\+\s*(\d+)', r'\1+\2', content, flags=re.IGNORECASE)

        # Fix broken f-strings across lines
        lines = content.splitlines()
        fixed_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            # Look for f-strings that might be broken across lines
            if 'f"' in line and line.count('"') % 2 == 1:  # Odd number of quotes
                # Check if next line completes the string
                if i + 1 < len(lines) and '"' in lines[i + 1]:"
                    # Merge the lines
                    merged = line.rstrip() + ' ' + lines[i + 1].lstrip()
                    fixed_lines.append(merged)
                    i += 2  # Skip next line
                    continue
            fixed_lines.append(line)
            i += 1
        content = '\n'.join(fixed_lines)

        # Fix trailing commas in function calls/definitions
        content = re.sub(r',\s*\)', ')', content)
        content = re.sub(r',\s*\]', ']', content)
        content = re.sub(r',\s*\}', '}', content)

        # Fix missing colons after control structures
        content = re.sub(r'^(\s*(?:if|elif|else|for|while|try|except|finally|with|def|class)\s+[^:]+)\s*$', r'\1:', content, flags=re.MULTILINE)

        # Normalize tabs to spaces
        content = content.expandtabs(4)

        return content

    def validate_syntax(self, content: str) -> Tuple[bool, Optional[str]]:
        """Validate Python syntax and return error if any."""
        try:
            ast.parse(content)
            return True, None
        except SyntaxError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Parse error: {e}"

    def call_llm_repair(self, file_path: Path, content: str, error_msg: str) -> Optional[str]:
        """Call Trae LLM to repair the file."""
        prompt = f"""Fix the syntax error in this Python file."""

File: {file_path}
Error: {error_msg}

Please return ONLY the corrected Python code, no explanations:

{content}""""""

        try:
            # Use subprocess to call the LLM
            process = subprocess.Popen(
                self.llm_cmd.split(),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
# BRACKET_SURGEON: disabled
#             )

            stdout, stderr = process.communicate(input=prompt, timeout=60)

            if process.returncode == 0 and stdout.strip():
                return stdout.strip()
            else:
                print(f"LLM error for {file_path}: {stderr}")
                return None

        except subprocess.TimeoutExpired:
            print(f"LLM timeout for {file_path}")
            process.kill()
            return None
        except Exception as e:
            print(f"LLM call failed for {file_path}: {e}")
            return None

    def backup_file(self, file_path: Path) -> Path:
        """Create a backup of the original file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f".py.bak.{timestamp}")
        shutil.copy2(file_path, backup_path)
        return backup_path

    def process_file(self, file_path: Path, dry_run: bool = False) -> bool:
        """Process a single Python file."""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            original_content = content

            # Step 1: Apply safe pre-fixes
            content = self.apply_safe_prefixes(content)

            # Check if pre-fixes solved the issue
            is_valid, error_msg = self.validate_syntax(content)

            if is_valid:
                if content != original_content:
                    if not dry_run:
                        self.backup_file(file_path)
                        file_path.write_text(content, encoding='utf-8')
                    print(f"✓ Pre-fixed: {file_path}")
                    self.stats['pre_fixed'] += 1
                    return True
                else:
                    # File was already valid
                    return True

            # Step 2: Use LLM for complex repairs
            print(f"⚠ Needs LLM repair: {file_path} - {error_msg}")

            llm_content = self.call_llm_repair(file_path, content, error_msg)
            if not llm_content:
                print(f"✗ LLM repair failed: {file_path}")
                self.stats['failed'] += 1
                return False

            # Validate LLM output
            is_valid, new_error = self.validate_syntax(llm_content)

            if not is_valid:
                # Retry once with new error
                print(f"⚠ LLM output still broken, retrying: {file_path} - {new_error}")
                retry_content = self.call_llm_repair(file_path, llm_content, new_error)

                if retry_content:
                    is_valid, _ = self.validate_syntax(retry_content)
                    if is_valid:
                        llm_content = retry_content

            if is_valid:
                if not dry_run:
                    self.backup_file(file_path)
                    file_path.write_text(llm_content, encoding='utf-8')
                print(f"✓ LLM fixed: {file_path}")
                self.stats['llm_fixed'] += 1
                return True
            else:
                # Save failed attempt
                if not dry_run:
                    failed_path = file_path.with_suffix('.failed.py')
                    failed_path.write_text(llm_content, encoding='utf-8')
                print(f"✗ Still broken after LLM: {file_path}")
                self.stats['failed'] += 1
                return False

        except Exception as e:
            print(f"✗ Error processing {file_path}: {e}")
            self.stats['failed'] += 1
            return False

    def find_python_files(self, root_dir: Path, only_backups: bool = False) -> List[Path]:
        """Find all Python files to process."""
        files = []

        for py_file in root_dir.rglob('*.py'):
            # Skip if in excluded directory
            if any(skip_dir in py_file.parts for skip_dir in SKIP_DIRS):
                continue

            # If only_backups is True, only process files in backup directories
            if only_backups:
                if not any(backup_dir in str(py_file) for backup_dir in ['url_fix_backups', 'copy_of_code', 'backups']):
                    continue

            files.append(py_file)

        return sorted(files)

    def run(self, root_dir: str, only_backups: bool = False, max_files: Optional[int] = None, dry_run: bool = False):
        """Run the batch rewriter."""
        root_path = Path(root_dir).resolve()

        if not root_path.exists():
            print(f"Error: Directory {root_path} does not exist")
            return 1

        print(f"Scanning for Python files in: {root_path}")
        if only_backups:
            print("Only processing backup directories")
        if dry_run:
            print("DRY RUN - No files will be modified")

        files = self.find_python_files(root_path, only_backups)

        if max_files:
            files = files[:max_files]
            print(f"Limited to first {max_files} files")

        print(f"Found {len(files)} Python files to process\n")

        for file_path in files:
            self.stats['processed'] += 1

            # Check if file already has syntax errors
            try:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                is_valid, _ = self.validate_syntax(content)
                if is_valid:
                    self.stats['skipped'] += 1
                    continue
            except:
                pass

            self.process_file(file_path, dry_run)

        # Print summary
        print(f"\n=== Summary ===")
        print(f"Processed: {self.stats['processed']}")
        print(f"Pre-fixed: {self.stats['pre_fixed']}")
        print(f"LLM fixed: {self.stats['llm_fixed']}")
        print(f"Failed: {self.stats['failed']}")
        print(f"Skipped (already valid): {self.stats['skipped']}")

        return 0 if self.stats['failed'] == 0 else 1

def main():
    parser = argparse.ArgumentParser(description='Trae Batch Rewriter - Fix Python syntax errors')
    parser.add_argument('directory', help='Root directory to scan for Python files')
    parser.add_argument('--only-backups', action='store_true', help='Only process backup directories')
    parser.add_argument('--max-files', type=int, help='Maximum number of files to process')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without making changes')
    parser.add_argument('--llm-cmd', default=None, help='Custom LLM command (overrides LLM_CMD env var)')

    args = parser.parse_args()

    # Determine LLM command
    llm_cmd = args.llm_cmd or os.environ.get('LLM_CMD', 'trae chat --model code-repair --stdin')

    rewriter = TraeBatchRewriter(llm_cmd)
    return rewriter.run(args.directory, args.only_backups, args.max_files, args.dry_run)

if __name__ == '__main__':
    sys.exit(main())