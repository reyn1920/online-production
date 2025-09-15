#!/usr/bin/env python3
"""
Find and fix unterminated docstrings by analyzing triple quote pairs
"""

import re

def find_unterminated_docstrings(file_path):
    """Find unterminated docstrings in the file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.split('\n')
    
    # Find all triple quote positions
    triple_quote_positions = []
    for i, line in enumerate(lines):
        if '"""' in line:
            # Count how many triple quotes are in this line
            count = line.count('"""')
            for _ in range(count):
                triple_quote_positions.append(i + 1)  # 1-indexed line numbers
    
    print(f"Found {len(triple_quote_positions)} triple quotes at lines: {triple_quote_positions}")
    
    # If odd number, find the unpaired one
    if len(triple_quote_positions) % 2 == 1:
        print("Odd number of triple quotes detected - there's an unterminated docstring")
        
        # Check each docstring pair
        in_docstring = False
        start_line = None
        
        for i, line in enumerate(lines):
            if '"""' in line:
                if not in_docstring:
                    # Starting a docstring
                    in_docstring = True
                    start_line = i + 1
                    print(f"Docstring starts at line {start_line}: {line.strip()}")
                else:
                    # Ending a docstring
                    in_docstring = False
                    print(f"Docstring ends at line {i + 1}: {line.strip()}")
                    start_line = None
        
        if in_docstring and start_line:
            print(f"UNTERMINATED DOCSTRING found starting at line {start_line}")
            return start_line
    
    return None

def fix_unterminated_docstring(file_path):
    """Fix the unterminated docstring"""
    unterminated_line = find_unterminated_docstrings(file_path)
    
    if unterminated_line:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add closing triple quotes at the end of the file
        if not content.endswith('\n'):
            content += '\n'
        content += '"""\n'
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"Added closing triple quotes to fix unterminated docstring")
        return True
    
    return False

if __name__ == "__main__":
    file_path = "backend/app.py"
    fix_unterminated_docstring(file_path)
    print("Unterminated docstring fix complete")