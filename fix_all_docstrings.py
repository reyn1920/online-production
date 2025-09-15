#!/usr/bin/env python3
"""
Comprehensive Docstring Fixer
Fixes all malformed docstring patterns in the backend codebase
"""

import os
import re
import glob

def fix_empty_docstrings(content):
    """Fix empty docstring patterns like '''\n\n\n'''"""
    # Pattern 1: Empty docstrings with whitespace
    pattern1 = r'"""\s*"""'
    content = re.sub(pattern1, '""""""', content)
    
    # Pattern 2: Docstrings with only newlines
    pattern2 = r'"""\n+"""'
    content = re.sub(pattern2, '""""""', content)
    
    # Pattern 3: Split docstrings (opening and closing on separate lines with content between)
    pattern3 = r'"""\n([^"]+)\n"""\n([^"\n]+)\n"""'
    def replace_split_docstring(match):
        title = match.group(1).strip()
        description = match.group(2).strip()
        return f'"""\n{title}\n\n{description}\n"""'
    content = re.sub(pattern3, replace_split_docstring, content, flags=re.MULTILINE | re.DOTALL)
    
    return content

def fix_malformed_class_docstrings(content):
    """Fix class docstrings that are outside the class definition"""
    # Pattern: class Name:\n    \n"""docstring"""\n\n    
    pattern = r'(class\s+\w+[^:]*:)\s*\n\s*\n"""([^"]+)"""\s*\n\s*\n\s*(def\s+__init__)'
    def replace_class_docstring(match):
        class_def = match.group(1)
        docstring = match.group(2).strip()
        init_def = match.group(3)
        return f'{class_def}\n    """\n    {docstring}\n    """\n    \n    {init_def}'
    
    content = re.sub(pattern, replace_class_docstring, content, flags=re.MULTILINE | re.DOTALL)
    return content

def fix_function_docstrings(content):
    """Fix function docstrings that are malformed"""
    # Pattern: def func():\n        \nDocstring text\n"""
    pattern = r'(def\s+\w+[^:]*:)\s*\n\s*\n([^"\n]+)\n"""'
    def replace_func_docstring(match):
        func_def = match.group(1)
        docstring = match.group(2).strip()
        return f'{func_def}\n        """\n        {docstring}\n        """'
    
    content = re.sub(pattern, replace_func_docstring, content, flags=re.MULTILINE)
    return content

def process_file(filepath):
    """Process a single Python file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all fixes
        content = fix_empty_docstrings(content)
        content = fix_malformed_class_docstrings(content)
        content = fix_function_docstrings(content)
        
        # Only write if changes were made
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Fixed: {filepath}")
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Main function to fix all Python files in backend"""
    backend_dir = 'backend'
    if not os.path.exists(backend_dir):
        print(f"Backend directory not found: {backend_dir}")
        return
    
    # Find all Python files
    python_files = glob.glob(os.path.join(backend_dir, '**', '*.py'), recursive=True)
    
    fixed_count = 0
    total_count = len(python_files)
    
    print(f"Processing {total_count} Python files...")
    
    for filepath in python_files:
        if process_file(filepath):
            fixed_count += 1
    
    print(f"\nCompleted: {fixed_count}/{total_count} files fixed")

if __name__ == '__main__':
    main()