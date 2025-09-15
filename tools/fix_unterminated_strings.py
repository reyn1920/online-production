#!/usr/bin/env python3
"""
Fix Unterminated String Literals Script
Automatically fixes unterminated triple-quoted strings across the backend codebase.
"""

import os
import re
import sys
from pathlib import Path

def fix_unterminated_strings(file_path):
    """Fix unterminated triple-quoted strings in a Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_made = 0
        
        # Pattern 1: Lines ending with triple quotes but not properly closed
        # Example: '''some text
        pattern1 = re.compile(r'^(.*?)"""([^"]*?)$', re.MULTILINE)
        matches = pattern1.findall(content)
        for prefix, text in matches:
            if text.strip() and not text.endswith('"""'):
                old_line = f'{prefix}"""{text}'
                new_line = f'{prefix}"""{text}"""'
                content = content.replace(old_line, new_line)
                fixes_made += 1
        
        # Pattern 2: Single line docstrings that are not properly closed
        # Example: """Some docstring text
        pattern2 = re.compile(r'^(\s*)"""([^"\n]+)$', re.MULTILINE)
        def replace_func(match):
            indent = match.group(1)
            text = match.group(2)
            return f'{indent}"""{text}"""'
        
        new_content = pattern2.sub(replace_func, content)
        if new_content != content:
            content = new_content
            fixes_made += len(pattern2.findall(original_content))
        
        # Pattern 3: Multi-line strings that start with triple quotes but don't end properly
        # Look for """ followed by content that doesn't end with """
        lines = content.split('\n')
        fixed_lines = []
        in_unclosed_string = False
        string_start_line = -1
        
        for i, line in enumerate(lines):
            if not in_unclosed_string:
                # Check if line starts a triple-quoted string
                if '"""' in line and line.count('"""') == 1:
                    # This might be the start of an unclosed string
                    in_unclosed_string = True
                    string_start_line = i
                fixed_lines.append(line)
            else:
                # We're inside an unclosed string, look for the end
                if '"""' in line:
                    # Found the end
                    in_unclosed_string = False
                    fixed_lines.append(line)
                elif line.strip() == '' or line.strip().startswith('#'):
                    # Empty line or comment, continue
                    fixed_lines.append(line)
                else:
                    # This might be the end of the unclosed string
                    # Check if this looks like code (not part of docstring)
                    if (line.strip().startswith(('def ', 'class ', 'import ', 'from ', 'if ', 'for ', 'while ', 'try:', 'except', 'return', '@')) or 
                        '=' in line or line.strip().endswith(':')):
                        # This is code, so we need to close the previous string
                        if string_start_line >= 0:
                            # Add closing quotes to the previous non-empty line
                            for j in range(len(fixed_lines) - 1, -1, -1):
                                if fixed_lines[j].strip():
                                    if not fixed_lines[j].rstrip().endswith('"""'):
                                        fixed_lines[j] = fixed_lines[j].rstrip() + '"""'
                                        fixes_made += 1
                                    break
                        in_unclosed_string = False
                    fixed_lines.append(line)
        
        # If we're still in an unclosed string at the end of file
        if in_unclosed_string and string_start_line >= 0:
            for j in range(len(fixed_lines) - 1, -1, -1):
                if fixed_lines[j].strip():
                    if not fixed_lines[j].rstrip().endswith('"""'):
                        fixed_lines[j] = fixed_lines[j].rstrip() + '"""'
                        fixes_made += 1
                    break
        
        content = '\n'.join(fixed_lines)
        
        # Write back if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return fixes_made
        
        return 0
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return 0

def main():
    """Main function to fix unterminated strings across the backend."""
    backend_dir = Path("/Users/thomasbrianreynolds/online production/backend")
    
    if not backend_dir.exists():
        print(f"Backend directory not found: {backend_dir}")
        return 1
    
    total_files = 0
    fixed_files = 0
    total_fixes = 0
    
    print("Fixing unterminated string literals...")
    
    # Process all Python files in backend directory
    for py_file in backend_dir.rglob("*.py"):
        total_files += 1
        fixes = fix_unterminated_strings(py_file)
        if fixes > 0:
            fixed_files += 1
            total_fixes += fixes
            print(f"Fixed {fixes} unterminated strings in {py_file.relative_to(backend_dir)}")
    
    print(f"\nSummary:")
    print(f"- Processed {total_files} files")
    print(f"- Fixed {fixed_files} files")
    print(f"- Total fixes: {total_fixes}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())