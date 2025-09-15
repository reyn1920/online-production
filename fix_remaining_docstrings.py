#!/usr/bin/env python3
"""
Comprehensive script to fix remaining docstring and syntax issues in the backend.
"""

import os
import re
import sys
from pathlib import Path

def fix_unterminated_docstrings(file_path):
    """Fix unterminated triple-quoted docstrings in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern 1: Fix unterminated docstrings that end with just quotes
        # Look for triple quotes followed by content but no closing quotes
        pattern1 = r'(\s*"""[^"]*?)\n(\s*(?:def |class |@|\w+\s*=|if |return |raise |import |from ))'  
        content = re.sub(pattern1, r'\1"""\n\2', content)
        
        # Pattern 2: Fix docstrings that are missing closing quotes at end of function/class
        pattern2 = r'(\s*"""[^"]*?)\n(\s*$)'
        content = re.sub(pattern2, r'\1"""\n\2', content, flags=re.MULTILINE)
        
        # Pattern 3: Fix malformed docstrings that have content after opening quotes
        pattern3 = r'(\s*""")([^"\n]+)\n((?:\s*[^"\n]+\n)*)(\s*)(?=def |class |@|\w+\s*=|if |return |raise |import |from |$)'
        def replace_func(match):
            indent = match.group(1).replace('"""', '')
            first_line = match.group(2)
            middle_content = match.group(3)
            last_indent = match.group(4)
            return f'{match.group(1)}{first_line}\n{middle_content}{indent}"""\n{last_indent}'
        
        content = re.sub(pattern3, replace_func, content)
        
        # Pattern 4: Fix standalone docstring lines that need closing
        lines = content.split('\n')
        fixed_lines = []
        in_docstring = False
        docstring_indent = ''
        
        for i, line in enumerate(lines):
            if '"""' in line and not in_docstring:
                # Starting a docstring
                if line.count('"""') == 1:  # Only opening quotes
                    in_docstring = True
                    docstring_indent = line[:line.index('"""')]
                    fixed_lines.append(line)
                else:  # Complete docstring on one line
                    fixed_lines.append(line)
            elif in_docstring:
                # Inside a docstring, look for natural ending points
                if (i + 1 < len(lines) and 
                    (lines[i + 1].strip().startswith(('def ', 'class ', '@', 'if ', 'return ', 'raise ')) or
                     lines[i + 1].strip() == '' or
                     re.match(r'^\s*\w+\s*=', lines[i + 1]))):
                    # This looks like the end of the docstring
                    fixed_lines.append(line)
                    fixed_lines.append(docstring_indent + '"""')
                    in_docstring = False
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
        
        # If we're still in a docstring at the end, close it
        if in_docstring:
            fixed_lines.append(docstring_indent + '"""')
        
        content = '\n'.join(fixed_lines)
        
        # Fix specific syntax issues
        # Fix bare "Features:" lines that should be in docstrings
        content = re.sub(r'^(\s*)Features:\s*$', r'\1"""\n\1Features:\n\1"""', content, flags=re.MULTILINE)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process all Python files in backend directory."""
    backend_dir = Path('backend')
    if not backend_dir.exists():
        print("Backend directory not found!")
        return 1
    
    fixed_files = []
    
    # Process all Python files
    for py_file in backend_dir.rglob('*.py'):
        if fix_unterminated_docstrings(py_file):
            fixed_files.append(str(py_file))
    
    print(f"Fixed docstring issues in {len(fixed_files)} files:")
    for file_path in fixed_files:
        print(f"  - {file_path}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())