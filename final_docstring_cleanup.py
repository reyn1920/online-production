#!/usr/bin/env python3

import re

def final_docstring_cleanup(file_path):
    """Final comprehensive cleanup of all docstring issues"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Remove all malformed docstring patterns
    patterns_to_remove = [
        # Standalone TODO docstrings
        r'\s*"""\s*\nTODO: Add docstring\s*\n"""\s*',
        # Empty docstrings
        r'\s*""""""\s*',
        # Orphaned TODO blocks
        r'\s*"""\s*\nTODO:[^"]*"""\s*',
        # Text outside quotes followed by docstrings
        r'\n\s*Get comprehensive marketing analytics dashboard data\.\s*\n\s*"""\s*\nTODO: Add docstring\s*\n"""\s*',
        # Multiple consecutive empty docstrings
        r'(\s*"""\s*\n){2,}',
        # Standalone text that should be in docstrings
        r'\nGet comprehensive marketing analytics dashboard data\.\s*\n',
        # Any remaining orphaned triple quotes
        r'\n\s*"""\s*\n(?=\s*def|\s*class|\s*async def|\s*@|\s*if|\s*try)',
    ]
    
    for pattern in patterns_to_remove:
        content = re.sub(pattern, '\n', content, flags=re.MULTILINE | re.DOTALL)
    
    # Clean up multiple consecutive newlines
    content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Fix any remaining malformed function definitions
    lines = content.split('\n')
    cleaned_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Skip lines that are just whitespace or malformed docstring remnants
        if line.strip() in ['"""', 'TODO: Add docstring', '']:
            # Check if this is between function definitions
            if i > 0 and i < len(lines) - 1:
                prev_line = lines[i-1].strip()
                next_line = lines[i+1].strip()
                
                # If we're between meaningful code, keep one empty line
                if (prev_line and not prev_line.startswith('#') and 
                    next_line and next_line.startswith(('def ', 'class ', 'async def ', '@'))):
                    cleaned_lines.append('')
            i += 1
            continue
            
        cleaned_lines.append(line)
        i += 1
    
    content = '\n'.join(cleaned_lines)
    
    # Final cleanup - remove any remaining orphaned quotes
    content = re.sub(r'^\s*"""\s*$', '', content, flags=re.MULTILINE)
    
    # Write back if changes were made
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Final cleanup completed for {file_path}")
        return True
    else:
        print(f"No changes needed in {file_path}")
        return False

if __name__ == '__main__':
    final_docstring_cleanup('backend/app.py')
    print("Final docstring cleanup complete")