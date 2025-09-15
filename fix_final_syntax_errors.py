#!/usr/bin/env python3
"""
Final script to fix remaining specific syntax errors.
"""

import os
import re
import sys
from pathlib import Path

def fix_file_syntax(file_path):
    """Fix specific syntax issues in a file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        lines = content.split('\n')
        fixed_lines = []
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Fix bare text at top of files that should be in docstrings
            if (i < 10 and  # Only check first 10 lines
                line.strip() and 
                not line.strip().startswith(('#', '"""', "'''", 'import ', 'from ', 'class ', 'def ', '@')) and
                not re.match(r'^\s*\w+\s*=', line) and
                not line.strip().startswith(('if ', 'try:', 'with ', 'for ', 'while '))):
                
                # This looks like documentation that should be in a docstring
                # Collect consecutive documentation lines
                doc_lines = []
                j = i
                while (j < len(lines) and 
                       lines[j].strip() and
                       not lines[j].strip().startswith(('#', '"""', "'''", 'import ', 'from ', 'class ', 'def ', '@')) and
                       not re.match(r'^\s*\w+\s*=', lines[j]) and
                       not lines[j].strip().startswith(('if ', 'try:', 'with ', 'for ', 'while '))):
                    doc_lines.append(lines[j])
                    j += 1
                
                if doc_lines:
                    # Convert to proper module docstring
                    fixed_lines.append('"""')
                    fixed_lines.extend(doc_lines)
                    fixed_lines.append('"""')
                    i = j
                    continue
            
            # Fix double triple quotes like """text"""""" 
            if '"""' in line:
                # Count quotes and fix if there are too many
                quote_count = line.count('"""')
                if quote_count > 2:
                    # Replace multiple triple quotes with just two (open and close)
                    parts = line.split('"""')
                    if len(parts) >= 3:
                        # Reconstruct with proper quotes
                        content_parts = [p for p in parts[1:-1] if p.strip()]
                        if content_parts:
                            line = parts[0] + '"""' + ''.join(content_parts) + '"""' + parts[-1]
                        else:
                            line = parts[0] + '""""""' + parts[-1]
            
            fixed_lines.append(line)
            i += 1
        
        content = '\n'.join(fixed_lines)
        
        # Additional regex fixes
        # Fix malformed docstrings with extra quotes
        content = re.sub(r'"""([^"]+)""""""', r'"""\1"""', content)
        
        # Fix cases where docstring content is on same line as quotes
        content = re.sub(r'"""([^"\n]+)""""""', r'"""\n\1\n"""', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to process problematic files."""
    # Target specific files that had errors
    problem_files = [
        'backend/routers/production_health.py',
        'backend/routers/social.py', 
        'backend/routers/davinci_resolve.py',
        'backend/middleware/timeout_middleware.py',
        'backend/database/chat_db.py',
        'backend/database/hypocrisy_db_manager.py'
    ]
    
    fixed_files = []
    
    for file_path in problem_files:
        if os.path.exists(file_path):
            if fix_file_syntax(file_path):
                fixed_files.append(file_path)
        else:
            print(f"File not found: {file_path}")
    
    # Also process any other Python files that might have similar issues
    backend_dir = Path('backend')
    if backend_dir.exists():
        for py_file in backend_dir.rglob('*.py'):
            if str(py_file) not in problem_files:
                if fix_file_syntax(py_file):
                    fixed_files.append(str(py_file))
    
    print(f"Fixed syntax issues in {len(fixed_files)} files:")
    for file_path in fixed_files:
        print(f"  - {file_path}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())