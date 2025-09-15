#!/usr/bin/env python3
""""""
Fix common syntax errors found in the codebase:
1. Unterminated f-strings with line breaks
2. F-strings with backslashes in expressions
3. Basic indentation issues
""""""

import re
import sys
from pathlib import Path

def fix_unterminated_fstrings(content: str) -> str:
    """Fix f-strings that are broken across lines."""
    # Pattern to match f-strings that are split across lines
    pattern = r'f"([^"]*{[^}]*\n[^}]*})([^"]*)"'
''

    def replace_func(match):
        # Join the f-string content on one line
        full_content = match.group(1) + match.group(2)
        # Remove internal newlines and extra spaces
        cleaned = re.sub(r'\n\s*', ' ', full_content)
        return f'f"{cleaned}"\n'

    return re.sub(pattern, replace_func, content, flags=re.MULTILINE)

def fix_fstring_backslashes(content: str) -> str:
    """Fix f-strings that contain backslashes in expressions."""
    lines = content.splitlines()
    fixed_lines = []

    for line in lines:
        # Look for f-strings with backslashes in expressions
        if 'f"' in line and '\\' in line and '{' in line:
            # Simple fix: convert to regular string formatting if possible
            if line.count('{') == 1 and line.count('}') == 1:
                # Extract the expression part
                start = line.find('{')
                end = line.find('}', start)
                if start != -1 and end != -1:
                    expr = line[start+1:end]
                    if '\\' in expr:'
                        # Replace with .format() style
                        new_line = line.replace('f"', '"').replace('{' + expr + '}', '{}')
                        # Add .format() at the end
                        if new_line.endswith('"'):"
                            new_line = new_line[:-1] + '".format(' + expr.replace('\\', '\\\\') + ')'"
                        elif new_line.endswith('")'):"
                            new_line = new_line[:-2] + '".format(' + expr.replace('\\', '\\\\') + '))'"
                        line = new_line
        fixed_lines.append(line)

    return '\n'.join(fixed_lines)

def fix_basic_indentation(content: str) -> str:
    """Fix basic indentation issues."""
    lines = content.splitlines()
    fixed_lines = []

    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            fixed_lines.append(line)
            continue

        # Check for lines that should be indented after certain keywords
        if i > 0:
            prev_line = lines[i-1].strip()
            if (prev_line.endswith(':') and
                any(prev_line.startswith(kw) for kw in ['if', 'else', 'elif', 'try', 'except', 'finally', 'for', 'while', 'def', 'class', 'with'])):
                # Current line should be indented
                if line and not line.startswith(' ') and not line.startswith('\t'):
                    line = '    ' + line

        fixed_lines.append(line)

    return '\n'.join(fixed_lines)

def fix_file(file_path: Path) -> bool:
    """Fix syntax errors in a single file."""
    try:
        content = file_path.read_text(encoding='utf-8', errors='ignore')
        original_content = content

        # Apply fixes
        content = fix_unterminated_fstrings(content)
        content = fix_fstring_backslashes(content)
        content = fix_basic_indentation(content)

        # Only write if content changed
        if content != original_content:
            file_path.write_text(content, encoding='utf-8')
            print(f"Fixed: {file_path}")
            return True
        return False

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to fix syntax errors."""
    project_root = Path.cwd()

    # Skip directories
    skip_dirs = {
        'url_fix_backups', 'copy_of_code', 'venv', 'venv_stable',
        'venv_creative', '.venv', 'node_modules', '.git', '__pycache__'
# BRACKET_SURGEON: disabled
#     }

    fixed_count = 0
    total_count = 0

    # Process all Python files
    for py_file in project_root.rglob('*.py'):
        # Skip if in excluded directory
        if any(skip_dir in py_file.parts for skip_dir in skip_dirs):
            continue

        total_count += 1
        if fix_file(py_file):
            fixed_count += 1

    print(f"\nProcessed {total_count} files, fixed {fixed_count} files")
    return 0

if __name__ == '__main__':
    sys.exit(main())