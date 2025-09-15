#!/usr/bin/env python3
""""""
Comprehensive Python Syntax Error Fixer

This script analyzes and fixes common Python syntax errors including:
- Indentation errors (unexpected indent, unindent mismatch, expected indented blocks)
- Unterminated string literals and f-string literals
- Unmatched parentheses, brackets, and braces
- Invalid syntax errors (decimal literals, character encoding, malformed expressions)

Usage:
    python comprehensive_syntax_fixer.py [--dry-run] [--backup] [--exclude dir1,dir2]
""""""

import os
import re
import ast
import sys
import shutil
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import tokenize
import io

class SyntaxErrorFixer:
    def __init__(self, dry_run=False, backup=True, exclude_dirs=None):
        self.dry_run = dry_run
        self.backup = backup
        self.exclude_dirs = exclude_dirs or []
        self.fixes_applied = 0
        self.files_processed = 0

        # Common patterns for fixing
        self.string_patterns = [
            # Unterminated strings
            (r'"([^"\\]*(\\.[^"\\]*)*)$', r'"\1"'),"
            (r"'([^'\\]*(\\.[^'\\]*)*)$", r"'\1'"),'
            # Unterminated f-strings
            (r'f"([^"\\]*(\\.[^"\\]*)*)$', r'f"\1"'),"
            (r"f'([^'\\]*(\\.[^'\\]*)*)$", r"f'\1'"),'
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         ]

        self.bracket_pairs = {'(': ')', '[': ']', '{': '}'}

    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if file should be excluded from processing"""
        path_str = str(file_path)

        # Exclude common directories
        exclude_patterns = [
            'venv', '__pycache__', '.git', '.trae', 'node_modules',
            '.pytest_cache', '.ruff_cache', 'test_output', 'test_results'
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         ] + self.exclude_dirs

        for pattern in exclude_patterns:
            if pattern in path_str:
                return True

        return False

    def find_python_files(self, directory: str) -> List[Path]:
        """Find all Python files in directory recursively"""
        python_files = []

        for root, dirs, files in os.walk(directory):
            # Remove excluded directories from dirs list to prevent traversal
            dirs[:] = [d for d in dirs if not any(excl in os.path.join(root, d) for excl in self.exclude_dirs)]

            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    if not self.should_exclude_file(file_path):
                        python_files.append(file_path)

        return python_files

    def backup_file(self, file_path: Path) -> None:
        """Create backup of file before modification"""
        if self.backup and not self.dry_run:
            backup_path = file_path.with_suffix(file_path.suffix + '.backup')
            shutil.copy2(file_path, backup_path)
            print(f"  📁 Backup created: {backup_path}")

    def fix_indentation_errors(self, content: str) -> Tuple[str, int]:
        """Fix common indentation errors"""
        lines = content.split('\n')
        fixed_lines = []
        fixes = 0

        for i, line in enumerate(lines):
            original_line = line

            # Fix mixed tabs and spaces (convert tabs to 4 spaces)
            if '\t' in line:
                line = line.expandtabs(4)
                fixes += 1

            # Fix common indentation patterns
            stripped = line.lstrip()
            if stripped:
                # Check for common patterns that need indentation
                if (stripped.startswith(('def ', 'class ', 'if ', 'elif ', 'else:', 'for ', 'while ', 'try:', 'except', 'finally:', 'with ')) and
                    i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].startswith(' ')):
                    # Next line should be indented
                    if i + 1 < len(lines):
                        next_line = lines[i + 1]
                        if next_line.strip() and not next_line.startswith(' '):
                            lines[i + 1] = '    ' + next_line
                            fixes += 1

            fixed_lines.append(line)

        return '\n'.join(fixed_lines), fixes

    def fix_unterminated_strings(self, content: str) -> Tuple[str, int]:
        """Fix unterminated string literals"""
        lines = content.split('\n')
        fixed_lines = []
        fixes = 0

        for line in lines:
            original_line = line

            # Check for unterminated strings at end of line
            stripped = line.rstrip()
            if stripped:
                # Simple heuristic: if line ends with quote but doesn't have matching quote
                if (stripped.endswith('"') and stripped.count('"') % 2 == 1) or \
                   (stripped.endswith("'") and stripped.count("'") % 2 == 1):
                    # This might be an unterminated string from previous line
                    pass

                # Look for obvious unterminated strings
                for pattern, replacement in self.string_patterns:
                    new_line = re.sub(pattern, replacement, line)
                    if new_line != line:
                        line = new_line
                        fixes += 1
                        break

            fixed_lines.append(line)

        return '\n'.join(fixed_lines), fixes

    def fix_unmatched_brackets(self, content: str) -> Tuple[str, int]:
        """Fix unmatched brackets, parentheses, and braces"""
        lines = content.split('\n')
        fixes = 0

        # Track bracket balance
        bracket_stack = []

        for i, line in enumerate(lines):
            for char in line:
                if char in self.bracket_pairs:
                    bracket_stack.append((char, i))
                elif char in self.bracket_pairs.values():
                    if bracket_stack:
                        open_bracket, _ = bracket_stack[-1]
                        if self.bracket_pairs[open_bracket] == char:
                            bracket_stack.pop()
                        else:
                            # Mismatched bracket - try to fix
                            bracket_stack.pop()
                            fixes += 1

        # Add missing closing brackets at the end
        while bracket_stack:
            open_bracket, line_num = bracket_stack.pop()
            closing_bracket = self.bracket_pairs[open_bracket]
            lines.append(closing_bracket)
            fixes += 1

        return '\n'.join(lines), fixes

    def fix_invalid_syntax(self, content: str) -> Tuple[str, int]:
        """Fix various invalid syntax issues"""
        fixes = 0

        # Fix common invalid syntax patterns
        patterns = [
            # Fix invalid decimal literals (leading zeros)
            (r'\b0+([1-9]\d*)\b', r'\1'),
            # Fix invalid characters in identifiers
            (r'[^\w\s]([a-zA-Z_]\w*)', r'\1'),
            # Fix malformed f-strings with backslashes
            (r'f"([^"]*\\\\[^"]*)*"', lambda m: f'f"{m.group(1).replace("\\\\", "\\n")}"'),"
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#         ]

        for pattern, replacement in patterns:
            if callable(replacement):
                content = re.sub(pattern, replacement, content)
            else:
                new_content = re.sub(pattern, replacement, content)
                if new_content != content:
                    content = new_content
                    fixes += 1

        return content, fixes

    def validate_syntax(self, content: str) -> Tuple[bool, Optional[str]]:
        """Validate Python syntax using AST"""
        try:
            ast.parse(content)
            return True, None
        except SyntaxError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Unexpected error: {str(e)}"

    def fix_file(self, file_path: Path) -> Dict[str, int]:
        """Fix syntax errors in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    original_content = f.read()
            except Exception as e:
                print(f"  ❌ Could not read {file_path}: {e}")
                return {'total_fixes': 0}

        content = original_content
        total_fixes = 0

        # Apply fixes in order
        content, indent_fixes = self.fix_indentation_errors(content)
        total_fixes += indent_fixes

        content, string_fixes = self.fix_unterminated_strings(content)
        total_fixes += string_fixes

        content, bracket_fixes = self.fix_unmatched_brackets(content)
        total_fixes += bracket_fixes

        content, syntax_fixes = self.fix_invalid_syntax(content)
        total_fixes += syntax_fixes

        # Validate the result
        is_valid, error_msg = self.validate_syntax(content)

        if total_fixes > 0:
            if self.dry_run:
                print(f"  🔧 Would fix {total_fixes} issues in {file_path}")
                if not is_valid:
                    print(f"    ⚠️  Syntax still invalid after fixes: {error_msg}")
            else:
                self.backup_file(file_path)
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"  ✅ Fixed {total_fixes} issues in {file_path}")
                if not is_valid:
                    print(f"    ⚠️  Syntax still invalid after fixes: {error_msg}")

        return {
            'total_fixes': total_fixes,
            'indent_fixes': indent_fixes,
            'string_fixes': string_fixes,
            'bracket_fixes': bracket_fixes,
            'syntax_fixes': syntax_fixes,
            'is_valid': is_valid
# BRACKET_SURGEON: disabled
#         }

    def process_directory(self, directory: str) -> None:
        """Process all Python files in directory"""
        print(f"🔍 Scanning for Python files in: {directory}")

        python_files = self.find_python_files(directory)
        print(f"📁 Found {len(python_files)} Python files to process")

        if self.dry_run:
            print("🧪 DRY RUN MODE - No files will be modified")

        total_fixes = 0
        files_with_fixes = 0

        for file_path in python_files:
            self.files_processed += 1
            print(f"\n📄 Processing: {file_path}")

            result = self.fix_file(file_path)
            if result['total_fixes'] > 0:
                files_with_fixes += 1
                total_fixes += result['total_fixes']

        print(f"\n📊 Summary:")
        print(f"   Files processed: {self.files_processed}")
        print(f"   Files with fixes: {files_with_fixes}")
        print(f"   Total fixes applied: {total_fixes}")

        if self.dry_run:
            print(f"\n💡 Run without --dry-run to apply fixes")

def main():
    parser = argparse.ArgumentParser(description='Fix Python syntax errors automatically')
    parser.add_argument('directory', nargs='?', default='.', help='Directory to process (default: current directory)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be fixed without making changes')
    parser.add_argument('--no-backup', action='store_true', help='Do not create backup files')
    parser.add_argument('--exclude', help='Comma-separated list of directories to exclude')

    args = parser.parse_args()

    exclude_dirs = []
    if args.exclude:
        exclude_dirs = [d.strip() for d in args.exclude.split(',')]

    fixer = SyntaxErrorFixer(
        dry_run=args.dry_run,
        backup=not args.no_backup,
        exclude_dirs=exclude_dirs
# FIXIT: commented possible stray closer
# FIXIT: commented possible stray closer
#     )

    try:
        fixer.process_directory(args.directory)
    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()