#!/usr/bin/env python3
"""
Fix invalid colons after field() declarations in dataclasses
"""

import os
import re
from pathlib import Path

def fix_field_colons(file_path):
    """Fix invalid colons after field() declarations"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to match field() declarations with invalid trailing colons
        pattern = r'(= field\([^)]+\)):'
        replacement = r'\1'
        
        content = re.sub(pattern, replacement, content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    backend_dir = Path("backend")
    files_fixed = 0
    total_fixes = 0
    
    # Process all Python files in backend directory
    for py_file in backend_dir.rglob("*.py"):
        if fix_field_colons(py_file):
            files_fixed += 1
            print(f"Fixed field colons in: {py_file}")
    
    print(f"\nCompleted: Fixed field colons in {files_fixed} files")

if __name__ == "__main__":
    main()