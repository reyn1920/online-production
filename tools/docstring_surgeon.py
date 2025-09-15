import os
import shutil
import argparse

def fix_unclosed_docstring(filepath, backup=False):
    """
    Specifically looks for unclosed triple-quote docstrings near the top of a file.
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
    except IOError:
        return False

    if not lines:
        return False
        
    # Check for unclosed docstring in the first 10 lines
    content_head = "".join(lines[:10])
    made_change = False
    
    if content_head.count('"""') == 1 or content_head.count("'''") == 1:
        quote_type = '"""' if '"""' in content_head else "'''"
        new_lines = []
        closed = False
        for line in lines:
            new_lines.append(line)
            if quote_type in line and not closed:
                # This is a very conservative fix. It adds the closing docstring
                # right after the line that opened it.
                new_lines.append(quote_type + '\n')
                closed = True
                made_change = True
        
        if made_change:
            print(f"Fixed potentially unclosed docstring in {filepath}")
            if backup:
                shutil.copy(filepath, filepath + '.bak_syn')
                print(f"  -> Created backup: {filepath}.bak_syn")

            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True
            
    return False

def main(target_dir, backup):
    """
    Walks the target directory and applies basic syntax fixes.
    """
    print(f"Running basic syntax normalization in: {target_dir}")
    fixed_file_count = 0
    
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                # Currently only implements the docstring fix.
                # Other normalizations (shebang, decimal literals) can be added here.
                if fix_unclosed_docstring(filepath, backup):
                    fixed_file_count += 1
    
    print(f"\nScan complete. Attempted fixes in {fixed_file_count} file(s).")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fix basic syntax issues like unclosed docstrings.")
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
    args = parser.parse_args()
    main(args.target_dir, args.backup)