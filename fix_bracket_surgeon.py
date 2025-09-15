#!/usr/bin/env python3
"""
Script to fix all BRACKET_SURGEON disabled comments across the codebase.
This script will uncomment all disabled brackets and parentheses.
"""

import os
import re
import sys
from pathlib import Path

def fix_bracket_surgeon_file(file_path):
    """Fix BRACKET_SURGEON disabled comments in a single file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Pattern to match BRACKET_SURGEON disabled comments and the following commented bracket/parenthesis
        # This handles cases like:
        # # BRACKET_SURGEON: disabled
        # #         )
        # or
        # # BRACKET_SURGEON: disabled
        # #             },
        
        # First, remove the BRACKET_SURGEON comment lines
        content = re.sub(r'^\s*# BRACKET_SURGEON: disabled\s*\n', '', content, flags=re.MULTILINE)
        
        # Then, uncomment the following lines that contain only brackets/braces/parentheses
        # Pattern matches lines like "#         )" or "#             }," or "#         ]"
        content = re.sub(r'^(\s*)#(\s*[\)\}\]],?\s*)$', r'\1\2', content, flags=re.MULTILINE)
        
        # Handle cases where the bracket is on the same line as the comment
        # Pattern like "# BRACKET_SURGEON: disabled }" or similar
        content = re.sub(r'# BRACKET_SURGEON: disabled\s*([\)\}\]],?)', r'\1', content)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def find_python_files(directory):
    """Find all Python files in the directory."""
    python_files = []
    for root, dirs, files in os.walk(directory):
        # Skip certain directories
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def main():
    """Main function to fix all BRACKET_SURGEON issues."""
    backend_dir = Path(__file__).parent / 'backend'
    
    if not backend_dir.exists():
        print(f"Backend directory not found: {backend_dir}")
        sys.exit(1)
    
    print(f"Scanning for Python files in: {backend_dir}")
    python_files = find_python_files(backend_dir)
    
    print(f"Found {len(python_files)} Python files")
    
    fixed_files = []
    for file_path in python_files:
        print(f"Processing: {file_path}")
        if fix_bracket_surgeon_file(file_path):
            fixed_files.append(file_path)
            print(f"  ✓ Fixed BRACKET_SURGEON issues")
        else:
            print(f"  - No changes needed")
    
    print(f"\nSummary:")
    print(f"  Total files processed: {len(python_files)}")
    print(f"  Files modified: {len(fixed_files)}")
    
    if fixed_files:
        print(f"\nModified files:")
        for file_path in fixed_files:
            print(f"  - {file_path}")
    
    print("\nBRACKET_SURGEON fix complete!")

if __name__ == '__main__':
    main()