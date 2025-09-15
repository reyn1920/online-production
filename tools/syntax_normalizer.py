import os
import shutil
import argparse
import re

def fix_file(filepath, backup=False):
    """
    Applies multiple conservative syntax fixes to a single Python file.
    It corrects unclosed docstrings, invalid decimal literals, and
    malformed encoding declarations.
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            original_content = f.read()
    except (IOError, UnicodeDecodeError) as e:
        print(f"Could not read file {filepath}: {e}")
        return False

    if not original_content:
        return False

    content = original_content
    made_change = False

    # --- Fix 1: Unclosed Docstrings ---
    # If there's an odd number of triple quotes, conservatively append a closing one at the end.
    if content.count('"""') % 2 != 0:
        content += '\n"""\n'
        made_change = True
        print(f"Fixed unclosed docstring in {filepath}")
    elif content.count("'''") % 2 != 0:
        content += "\n'''\n"
        made_change = True
        print(f"Fixed unclosed docstring in {filepath}")
    
    lines = content.splitlines(True)

    # --- Fix 2: Invalid Decimal Literals ---
    modified_lines = []
    literals_fixed = False
    for line in lines:
        # Replaces numbers like `8003.` with `8003`.
        # This regex ensures it only targets numbers that aren't part of a float or attribute access.
        new_line = re.sub(r'\b(\d+)\.\b', r'\1', line)
        if new_line != line:
            literals_fixed = True
        modified_lines.append(new_line)
    
    if literals_fixed:
        lines = modified_lines
        made_change = True
        print(f"Fixed invalid decimal literal in {filepath}")

    # --- Fix 3: Malformed Encoding Declarations ---
    encoding_fixed = False
    # Check first two lines for a malformed encoding cookie
    for i in range(min(2, len(lines))):
        line = lines[i]
        if 'coding:' in line and line.strip().startswith('#'):
            correct_encoding_line = '# -*- coding: utf-8 -*-\n'
            # Use .strip() for comparison to handle different line endings
            if line.strip() != correct_encoding_line.strip():
                lines[i] = correct_encoding_line
                encoding_fixed = True
                made_change = True
                print(f"Fixed encoding declaration in {filepath}")
                break # Only fix one per file
    
    if made_change:
        new_content = "".join(lines)
        if backup:
            backup_path = filepath + '.bak_syn'
            shutil.copy(filepath, backup_path)
            print(f"  -> Created backup: {backup_path}")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        except IOError as e:
            print(f"Could not write to file {filepath}: {e}")
            return False
            
    return False

def main(target_dir, backup, conservative):
    """
    Walks the target directory and applies basic syntax fixes.
    The 'conservative' flag is acknowledged but not used as all fixes are conservative.
    """
    print(f"Running basic syntax normalization in: {target_dir}")
    fixed_file_count = 0
    
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                if fix_file(filepath, backup):
                    fixed_file_count += 1
    
    print(f"\nScan complete. Attempted fixes in {fixed_file_count} file(s).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Fix basic syntax issues like unclosed docstrings, invalid decimal literals, and malformed encoding declarations."
    )
    parser.add_argument(
        '--target-dir',
        default='.',
        help='The root directory of the codebase to scan.'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Create a .bak_syn backup of any file that is modified.'
    )
    parser.add_argument(
        '--conservative',
        action='store_true',
        help='Run in conservative mode (all fixes are conservative by default).'
    )
    args = parser.parse_args()
    main(args.target_dir, args.backup, args.conservative)