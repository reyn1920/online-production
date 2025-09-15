#!/usr/bin/env python3
"""
Fix all unterminated docstrings in app.py
"""

import re

def fix_unterminated_docstrings(file_path):
    """Fix all unterminated docstrings in the given file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern 1: Fix docstrings that start with """ but don't close properly
    # Look for lines with single """ that should be closed
    lines = content.split('\n')
    fixed_lines = []
    in_docstring = False
    docstring_indent = ''
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Check if this line starts a docstring
        if '"""' in line and not in_docstring:
            quote_count = line.count('"""')
            if quote_count == 1:  # Opening docstring
                in_docstring = True
                docstring_indent = line[:line.index('"""')]
                # If the line has content after """, it might be a single-line docstring
                after_quotes = line[line.index('"""') + 3:].strip()
                if after_quotes and not after_quotes.startswith('"'):
                    # This is likely an unterminated single-line docstring
                    fixed_lines.append(line + '"""')
                    in_docstring = False
                else:
                    fixed_lines.append(line)
            elif quote_count == 2:  # Complete docstring on one line
                fixed_lines.append(line)
            else:  # Odd number > 1, likely malformed
                fixed_lines.append(line)
        elif in_docstring:
            # We're inside a docstring, look for closing
            if '"""' in line:
                in_docstring = False
                fixed_lines.append(line)
            else:
                # Check if this line looks like it should end the docstring
                if (stripped.startswith(('def ', 'class ', '@', 'async def ')) or 
                    stripped.startswith(('return ', 'try:', 'if ', 'for ', 'while ')) or
                    stripped == '' and i + 1 < len(lines) and 
                    lines[i + 1].strip().startswith(('def ', 'class ', '@', 'async def '))):
                    # End the docstring before this line
                    fixed_lines.append(docstring_indent + '"""')
                    fixed_lines.append(line)
                    in_docstring = False
                else:
                    fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    # If we're still in a docstring at the end, close it
    if in_docstring:
        fixed_lines.append(docstring_indent + '"""')
    
    # Join back and apply additional fixes
    content = '\n'.join(fixed_lines)
    
    # Pattern 2: Fix specific malformed patterns
    # Fix cases where docstring content is on the same line as opening quotes
    content = re.sub(r'(\s*""")(\s*[^"\n]+)(\s*)$', r'\1\n\1\2\n\1"""', content, flags=re.MULTILINE)
    
    # Pattern 3: Fix empty docstrings that are just """
    content = re.sub(r'^(\s*)"""\s*$', r'\1"""\n\1TODO: Add docstring\n\1"""', content, flags=re.MULTILINE)
    
    return content

if __name__ == '__main__':
    file_path = 'backend/app.py'
    print(f"Fixing unterminated docstrings in {file_path}...")
    
    try:
        fixed_content = fix_unterminated_docstrings(file_path)
        
        # Write the fixed content back
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        print("✅ Fixed unterminated docstrings")
        
        # Test syntax
        import ast
        try:
            ast.parse(fixed_content)
            print("✅ Syntax validation passed")
        except SyntaxError as e:
            print(f"❌ Syntax error still exists: {e}")
            print(f"   Line {e.lineno}: {e.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")