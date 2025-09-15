#!/usr/bin/env python3
# Purpose: add missing ":" to def/class lines with Pythonic signature shapes.

import os, re, sys, shutil, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".venv", "venv", "__pycache__", "node_modules", "dist", "build"}

DEF_RE = re.compile(r'^(\s*def\s+\w+\s*\([^)]*\)\s*)(#.*)?$')
CLS_RE = re.compile(r'^(\s*class\s+\w+(?:\s*\([^)]*\))?\s*)(#.*)?$')

def pyfiles(root: Path):
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            if f.endswith(".py"):
                yield Path(dp) / f

def fix_file(filepath, backup=False):
    """
    Scans a file for class or function definitions that are missing
    a closing colon and adds it. This version is enhanced to correctly
    handle multiline signatures and decorators.
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except IOError:
        print(f"Could not read file: {filepath}")
        return False

    if not lines:
        return False
    
    made_change = False
    new_lines = list(lines)  # Create a mutable copy
    i = 0
    while i < len(new_lines):
        # Find the actual start of the signature, skipping decorators
        start_line_index = i
        current_line_stripped = new_lines[start_line_index].lstrip()
        while current_line_stripped.startswith('@'):
            start_line_index += 1
            if start_line_index >= len(new_lines):
                current_line_stripped = ''
                break
            current_line_stripped = new_lines[start_line_index].lstrip()

        if start_line_index >= len(new_lines):
            break # Reached end of file
        
        # Check if the line looks like the start of a function/class definition
        if current_line_stripped.startswith(('def ', 'class ')):
            paren_level = 0
            signature_end_line_index = -1
            signature_started = False

            # Scan from this line forward to find the end of the signature
            for j in range(start_line_index, len(new_lines)):
                scan_line = new_lines[j]
                
                # Basic handling to ignore brackets within strings
                in_string_char = None
                for char in scan_line:
                    if in_string_char:
                        if char == in_string_char:
                            in_string_char = None
                    elif char in ('"', "'"):
                        in_string_char = char
                    elif not in_string_char:
                        if char == '(':
                            paren_level += 1
                            signature_started = True
                        elif char == ')':
                            paren_level -= 1
                
                # When paren_level is 0 after being > 0, the signature has closed.
                if signature_started and paren_level == 0:
                    signature_end_line_index = j
                    break

            if signature_end_line_index != -1:
                # We found the line where the signature ends. Let's check it for a colon.
                end_line = new_lines[signature_end_line_index]
                stripped_end_line = end_line.rstrip()

                # Ignore comments at the end of the line
                code_part = stripped_end_line
                if '#' in code_part:
                    code_part = code_part.split('#', 1)[0].rstrip()

                if code_part and not code_part.endswith(':'):
                    # Colon is missing. Add it.
                    # We add it before the comment if one exists.
                    if '#' in stripped_end_line:
                        parts = stripped_end_line.split('#', 1)
                        new_line_content = parts[0].rstrip() + ': #' + parts[1]
                    else:
                        new_line_content = stripped_end_line + ':'
                    
                    new_lines[signature_end_line_index] = new_line_content + '\n'
                    print(f"Added missing colon in {filepath} on line {signature_end_line_index + 1}")
                    made_change = True
                    i = signature_end_line_index # Skip ahead to prevent re-processing
        
        i += 1

    if made_change:
        if backup:
            shutil.copy(filepath, filepath + '.bak_colon')
            print(f"  -> Created backup: {filepath}.bak_colon")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        return True
    
    return False

def fix_line(ln: str) -> str:
    if DEF_RE.match(ln) and not ln.rstrip().endswith(":"):
        return ln.rstrip() + ":"
    if CLS_RE.match(ln) and not ln.rstrip().endswith(":"):
        return ln.rstrip() + ":"
    return ln

def main(target_dir, backup):
    print(f"Scanning for missing colons in function/class definitions in: {target_dir}")
    fixed_file_count = 0
    
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_file(filepath, backup):
                    fixed_file_count += 1
    
    print(f"\nScan complete. Attempted fixes in {fixed_file_count} file(s).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add missing colons to def/class lines. Handles multiline signatures.")
    parser.add_argument(
        '--target-dir', default='.', help='The root directory to scan.'
    )
    parser.add_argument(
        '--backup', action='store_true', help='Create a .bak_colon backup of modified files.'
    )
    args = parser.parse_args()
    main(args.target_dir, args.backup)