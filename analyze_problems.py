#!/usr/bin/env python3
"""
Analyze Python syntax errors and problems in the codebase
"""

import ast
import os
import sys
from pathlib import Path

def find_syntax_errors():
    """Find all Python files with syntax errors"""
    errors = []
    python_files = []
    
    # Find all Python files
    for root, dirs, files in os.walk('.'):
        # Skip common directories
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.venv', 'venv', 'node_modules'}]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files")
    
    # Check each file for syntax errors
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            try:
                ast.parse(content)
            except SyntaxError as e:
                errors.append((file_path, f"SyntaxError: {e.msg} (line {e.lineno})"))
            except Exception as e:
                errors.append((file_path, f"ParseError: {str(e)}"))
                
        except Exception as e:
            errors.append((file_path, f"FileError: {str(e)}"))
    
    return errors, len(python_files)

def main():
    print("🔍 Analyzing Python codebase for problems...")
    
    errors, total_files = find_syntax_errors()
    
    print(f"\n📊 ANALYSIS RESULTS:")
    print(f"Total Python files: {total_files}")
    print(f"Files with syntax errors: {len(errors)}")
    print(f"Success rate: {((total_files - len(errors)) / total_files * 100):.1f}%")
    
    if errors:
        print(f"\n❌ FILES WITH SYNTAX ERRORS ({len(errors)} total):")
        for i, (file_path, error) in enumerate(errors[:50], 1):
            print(f"{i:3d}. {file_path}")
            print(f"     {error}")
        
        if len(errors) > 50:
            print(f"     ... and {len(errors) - 50} more files")
    
    # Categorize error types
    error_types = {}
    for _, error in errors:
        error_type = error.split(':')[0] if ':' in error else 'Unknown'
        error_types[error_type] = error_types.get(error_type, 0) + 1
    
    if error_types:
        print(f"\n📈 ERROR TYPE BREAKDOWN:")
        for error_type, count in sorted(error_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {error_type}: {count} files")

if __name__ == "__main__":
    main()