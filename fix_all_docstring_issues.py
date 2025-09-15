#!/usr/bin/env python3

import re

def fix_unterminated_docstrings(file_path):
    """Fix all unterminated docstrings in the file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Find all triple quote positions
    triple_quotes = []
    for match in re.finditer(r'"""', content):
        triple_quotes.append(match.start())
    
    # Check if we have an odd number of triple quotes (indicating unterminated strings)
    if len(triple_quotes) % 2 != 0:
        print(f"Found {len(triple_quotes)} triple quotes (odd number - indicates unterminated strings)")
        
        # Find lines that start docstrings but don't have closing quotes
        lines = content.split('\n')
        in_docstring = False
        docstring_start_line = -1
        
        for i, line in enumerate(lines):
            # Count triple quotes in this line
            quote_count = line.count('"""')
            
            if quote_count == 1:
                if not in_docstring:
                    # Starting a docstring
                    in_docstring = True
                    docstring_start_line = i
                else:
                    # Ending a docstring
                    in_docstring = False
            elif quote_count == 2:
                # Single-line docstring, no change needed
                pass
            elif quote_count > 2:
                # Multiple quotes in one line, might need fixing
                pass
        
        # If we're still in a docstring at the end, we need to close it
        if in_docstring:
            print(f"Found unterminated docstring starting at line {docstring_start_line + 1}")
            # Add closing quotes at the end of the file
            content = content.rstrip() + '\n"""\n'
    
    # Additional cleanup patterns
    # Remove standalone TODO docstrings
    content = re.sub(r'\s*"""\s*\nTODO: Add docstring\s*\n"""\s*', '\n', content)
    
    # Remove empty docstrings
    content = re.sub(r'\s*""""""\s*', '', content)
    
    # Fix malformed docstrings in HTML returns
    content = re.sub(r'return """\s*"""\s*TODO: Add docstring\s*"""', 'return """', content)
    
    # Write back if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed unterminated docstrings in {file_path}")
        return True
    else:
        print(f"No changes needed in {file_path}")
        return False

if __name__ == '__main__':
    fix_unterminated_docstrings('backend/app.py')
    print("Docstring fix complete")