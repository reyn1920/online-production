#!/usr/bin/env python3
"""
Comprehensive docstring fix script for app.py
Finds and fixes all malformed docstrings that cause syntax errors
"""

import re

def fix_all_docstring_issues(file_path):
    """Fix all docstring-related syntax issues in the file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern 1: Fix standalone text that should be docstrings (after function definitions)
    # Look for function definitions followed by unquoted text
    pattern1 = r'(def\s+\w+\([^)]*\):\s*\n\s*)([A-Z][^"\n]+)\s*\n'
    matches1 = re.findall(pattern1, content)
    for match in matches1:
        func_def, text = match
        old_text = func_def + text + '\n'
        new_text = func_def + f'"""{ text.strip()}"""\n'
        content = content.replace(old_text, new_text)
        print(f"Fixed unquoted docstring: {text.strip()[:50]}...")
    
    # Pattern 2: Fix async function definitions with unquoted text
    pattern2 = r'(async\s+def\s+\w+\([^)]*\):\s*\n\s*)([A-Z][^"\n]+)\s*\n'
    matches2 = re.findall(pattern2, content)
    for match in matches2:
        func_def, text = match
        old_text = func_def + text + '\n'
        new_text = func_def + f'"""{ text.strip()}"""\n'
        content = content.replace(old_text, new_text)
        print(f"Fixed async unquoted docstring: {text.strip()[:50]}...")
    
    # Pattern 3: Remove standalone TODO comments that are malformed
    content = re.sub(r'\s*"""\s*TODO:[^"]*"""\s*\n', '\n', content)
    
    # Pattern 4: Fix empty docstrings
    content = re.sub(r'"""\s*"""', '"""Function docstring"""', content)
    
    # Pattern 5: Fix malformed triple quotes
    content = re.sub(r'""""""', '"""', content)
    
    # Pattern 6: Remove orphaned closing triple quotes
    content = re.sub(r'^\s*"""\s*$', '', content, flags=re.MULTILINE)
    
    # Clean up excessive newlines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed docstring issues in {file_path}")
        return True
    else:
        print(f"No docstring issues found in {file_path}")
        return False

if __name__ == "__main__":
    file_path = "backend/app.py"
    fix_all_docstring_issues(file_path)
    print("Comprehensive docstring fix complete")