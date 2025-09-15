#!/usr/bin/env python3
"""
Final targeted script to fix malformed docstrings with text before triple quotes.
"""

import os
import re
import sys
from pathlib import Path

def fix_malformed_docstrings(file_path):
    """Fix malformed docstrings where text appears before triple quotes."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Pattern: text before triple quotes like 'Some text"""'
            if '"""' in line and not line.strip().startswith('"""'):
                # Check if there's text before the triple quotes
                quote_pos = line.find('"""')
                if quote_pos > 0:
                    before_quotes = line[:quote_pos].strip()
                    after_quotes = line[quote_pos + 3:]
                    
                    # If there's meaningful text before quotes, it's likely a malformed docstring
                    if (before_quotes and 
                        not before_quotes.endswith(('=', '(', '[', '{', '+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=')) and
                        not re.match(r'^\s*(def|class|if|elif|else|try|except|finally|with|for|while|return|yield|raise|import|from)\b', before_quotes)):
                        
                        # Get the indentation from the original line
                        indent = line[:len(line) - len(line.lstrip())]
                        
                        # Reconstruct as proper docstring
                        if after_quotes.strip():
                            # There's content after the quotes too
                            fixed_lines.append(f'{indent}"""')
                            fixed_lines.append(f'{indent}{before_quotes}')
                            if after_quotes.strip() != '"""':
                                fixed_lines.append(f'{indent}{after_quotes.strip()}')
                            fixed_lines.append(f'{indent}"""')
                        else:
                            # Just text before quotes
                            fixed_lines.append(f'{indent}"""')
                            fixed_lines.append(f'{indent}{before_quotes}')
                            fixed_lines.append(f'{indent}"""')
                        continue
            
            # Pattern: lines ending with triple quotes that should be closed
            if line.strip().endswith('"""') and not line.strip().startswith('"""'):
                # Check if this is a single-line docstring or needs closing
                if line.count('"""') == 1:
                    # This might be an unclosed docstring
                    # Look ahead to see if there's a natural break
                    if (i + 1 < len(lines) and 
                        (lines[i + 1].strip() == '' or
                         lines[i + 1].strip().startswith(('def ', 'class ', '@', 'if ', 'return ', 'import ', 'from ')))):
                        # Add closing quotes
                        indent = line[:len(line) - len(line.lstrip())]
                        fixed_lines.append(line)
                        fixed_lines.append(f'{indent}"""')
                        continue
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Additional regex-based fixes for common patterns
        # Fix: text""" -> """\ntext\n"""
        content = re.sub(r'^(\s*)([^"\n]+)"""\s*$', r'\1"""\n\1\2\n\1"""', content, flags=re.MULTILINE)
        
        # Fix: """text"""more_text""" -> """\ntext\nmore_text\n"""
        content = re.sub(r'"""([^"]+)"""([^"]+)"""', r'"""\n\1\n\2\n"""', content)
        
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
        if fix_malformed_docstrings(py_file):
            fixed_files.append(str(py_file))
    
    print(f"Fixed malformed docstring syntax in {len(fixed_files)} files:")
    for file_path in fixed_files:
        print(f"  - {file_path}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())