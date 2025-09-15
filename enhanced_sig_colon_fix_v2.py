import os
import shutil
import argparse
import re

def fix_file(filepath, backup=False):
    """
    Scans a file for class or function definitions that are missing
    a closing colon and adds it. This production-grade version uses an
    advanced state machine to handle multiline signatures, decorators,
    complex type hints, all string types, and comments.
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
            break  # Reached end of file
        
        # Check if the line looks like the start of a function/class definition
        if current_line_stripped.startswith(('def ', 'class ')):
            # State machine variables
            paren_level = 0
            bracket_level = 0
            brace_level = 0
            in_string_char = None
            in_multiline_string_type = None # Will hold '"""' or "'''"
            
            signature_end_line_index = -1
            signature_started = False

            # Scan from this line forward to find the precise end of the signature
            for j in range(start_line_index, len(new_lines)):
                scan_line = new_lines[j]
                
                k = 0
                while k < len(scan_line):
                    # Check for multiline string start/end first
                    if scan_line[k:k+3] == '"""' and not in_string_char:
                        in_multiline_string_type = None if in_multiline_string_type == '"""' else '"""'
                        k += 2 # Advance past the token
                    elif scan_line[k:k+3] == "'''" and not in_string_char:
                        in_multiline_string_type = None if in_multiline_string_type == "'''" else "'''"
                        k += 2 # Advance past the token
                    
                    # If inside any string, check for single-line string toggles
                    elif not in_multiline_string_type:
                        char = scan_line[k]
                        # Handle escaped characters by just skipping them
                        if (in_string_char) and char == '\\':
                            k += 1 # Skip this char and the next
                        elif char in ('"', "'"):
                            if not in_string_char:
                                in_string_char = char
                            elif in_string_char == char:
                                in_string_char = None
                        
                        # Process comments and brackets only if not inside any string
                        elif not in_string_char:
                            if char == '#':
                                break  # Skip the rest of the line
                            
                            if char == '(':
                                paren_level += 1
                                signature_started = True
                            elif char == ')':
                                paren_level -= 1
                            elif char == '[':
                                bracket_level += 1
                            elif char == ']':
                                bracket_level -= 1
                            elif char == '{':
                                brace_level += 1
                            elif char == '}':
                                brace_level -= 1
                    k += 1

                # Signature ends when all bracket types are balanced, triggered by the main parentheses closing
                if signature_started and paren_level == 0 and bracket_level == 0 and brace_level == 0:
                    signature_end_line_index = j
                    break
            
            if signature_end_line_index != -1:
                # We found the line where the signature ends. Let's check it for a colon.
                end_line = new_lines[signature_end_line_index]
                stripped_end_line = end_line.rstrip()

                code_part = stripped_end_line
                if '#' in code_part:
                    code_part = code_part.split('#', 1)[0].rstrip()

                if code_part and not code_part.endswith(':'):
                    # Colon is missing. Add it before the comment if one exists.
                    if '#' in stripped_end_line:
                        parts = stripped_end_line.split('#', 1)
                        new_line_content = parts[0].rstrip() + ': #' + parts[1]
                    else:
                        new_line_content = stripped_end_line + ':'
                    
                    new_lines[signature_end_line_index] = new_line_content + '\n'
                    print(f"Added missing colon in {filepath} on line {signature_end_line_index + 1}")
                    made_change = True
                    i = signature_end_line_index  # Skip ahead to prevent re-processing
        
        i += 1

    if made_change:
        if backup:
            shutil.copy(filepath, filepath + '.bak_colon')
            print(f"  -> Created backup: {filepath}.bak_colon")

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True
        except IOError:
            print(f"Could not write to file: {filepath}")
            return False
    
    return False

def main(target_dir='.', backup=False):
    """
    Main function to scan directory and fix missing colons in Python files.
    """
    files_processed = 0
    files_fixed = 0
    
    for root, dirs, files in os.walk(target_dir):
        # Skip common directories that shouldn't be processed
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'venv', '.venv']]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                files_processed += 1
                
                if fix_file(filepath, backup):
                    files_fixed += 1
    
    print(f"\nProcessed {files_processed} Python files, fixed {files_fixed} files.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Fix missing colons in Python function/class definitions with enhanced multiline signature and decorator handling'
    )
    parser.add_argument('--target-dir', default='.', help='Target directory to scan (default: current directory)')
    parser.add_argument('--backup', action='store_true', help='Create backup files before making changes')
    
    args = parser.parse_args()
    main(args.target_dir, args.backup)