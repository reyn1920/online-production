#!/usr/bin/env python3
"""
Unterminated String Literal Fixer

Specialized script to fix unterminated string literals in Python files.
"""

import os
import re
import ast
from pathlib import Path
from typing import List, Tuple

# Directories to exclude from processing
EXCLUDE_DIRS = {
    'venv', 'venv_stable', 'venv_creative', '__pycache__', '.git', 'node_modules', 
    'models', '.pytest_cache', 'dist', 'build', '.tox'
}

class UnterminatedStringFixer:
    def __init__(self):
        self.fixed_files = []
        self.failed_files = []
        
    def fix_docstring_issues(self, content: str) -> str:
        """Fix common docstring issues"""
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            fixed_line = line
            
            # Fix quadruple quotes to triple quotes
            if '""""' in line:
                fixed_line = line.replace('""""', '"""')
            
            # Fix missing opening quotes in docstrings
            if line.strip() == '""""' or line.strip() == "''''":
                if line.strip() == '""""':
                    fixed_line = line.replace('""""', '"""')
                elif line.strip() == "''''":
                    fixed_line = line.replace("''''", "'''")
            
            fixed_lines.append(fixed_line)
        
        return '\n'.join(fixed_lines)
    
    def fix_string_patterns(self, content: str) -> str:
        """Fix specific string patterns found in the codebase"""
        
        # Fix missing quotes around function parameters and dictionary keys
        # Pattern: function(parameter) -> function("parameter")
        content = re.sub(r'\b(get|append|execute|connect)\(([a-zA-Z_][a-zA-Z0-9_.]*)\)', r'\1("\2")', content)
        
        # Fix missing quotes in print statements with f-strings
        content = re.sub(r'printf"([^"]*)}([^"]*)}([^"]*)"\)', r'print(f"\1{\2}\3")', content)
        content = re.sub(r'printf"([^"]*)}([^"]*)"\)', r'print(f"\1{\2}")', content)
        
        # Fix missing quotes in dictionary literals
        content = re.sub(r'\{([a-zA-Z_][a-zA-Z0-9_]*):([^}"\']*)\}', r'{"\1": "\2"}', content)
        
        # Fix missing quotes in list comprehensions and conditions
        content = re.sub(r'in \[([^\]"\']*)\]', r'in ["\1"]', content)
        
        return content
    
    def fix_method_calls(self, content: str) -> str:
        """Fix method calls with missing quotes"""
        # Fix self.method calls with missing quotes
        content = re.sub(r'self\.([a-zA-Z_][a-zA-Z0-9_]*)\(([a-zA-Z_][a-zA-Z0-9_.]*)\)', r'self.\1("\2")', content)
        
        # Fix object.method calls with missing quotes  
        content = re.sub(r'([a-zA-Z_][a-zA-Z0-9_]*)\.([a-zA-Z_][a-zA-Z0-9_]*)\(([a-zA-Z_][a-zA-Z0-9_.]*)\)', r'\1.\2("\3")', content)
        
        return content
    
    def can_parse_file(self, content: str) -> bool:
        """Check if file can be parsed as valid Python"""
        try:
            ast.parse(content)
            return True
        except SyntaxError:
            return False
    
    def fix_file(self, file_path: Path) -> bool:
        """Fix unterminated strings in a single file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Skip if file is already valid
            if self.can_parse_file(original_content):
                return True
            
            # Apply fixes in order
            fixed_content = original_content
            fixed_content = self.fix_docstring_issues(fixed_content)
            fixed_content = self.fix_string_patterns(fixed_content)
            fixed_content = self.fix_method_calls(fixed_content)
            
            # Verify the fix worked
            if self.can_parse_file(fixed_content):
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                print(f"✅ Fixed: {file_path}")
                self.fixed_files.append(str(file_path))
                return True
            else:
                print(f"⚠️  Could not fix: {file_path}")
                self.failed_files.append(str(file_path))
                return False
                
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            self.failed_files.append(str(file_path))
            return False
    
    def process_directory(self, root_path: Path) -> None:
        """Process all Python files in directory"""
        print(f"🔍 Scanning for Python files in {root_path}...")
        
        python_files = []
        for root, dirs, files in os.walk(root_path):
            # Prune excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = Path(root) / file
                    # Skip files that are already working
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        if not self.can_parse_file(content):
                            python_files.append(file_path)
                    except:
                        python_files.append(file_path)
        
        print(f"📁 Found {len(python_files)} Python files with syntax errors")
        
        for file_path in python_files:
            self.fix_file(file_path)
    
    def print_summary(self):
        """Print summary of fixes"""
        print("\n" + "="*50)
        print("UNTERMINATED STRING FIX SUMMARY")
        print("="*50)
        print(f"✅ Files fixed: {len(self.fixed_files)}")
        print(f"❌ Files failed: {len(self.failed_files)}")
        
        if self.failed_files:
            print("\n❌ Failed files:")
            for file in self.failed_files[:10]:  # Show first 10
                print(f"  - {file}")
            if len(self.failed_files) > 10:
                print(f"  ... and {len(self.failed_files) - 10} more")

def main():
    """Main function"""
    root_path = Path('.')
    fixer = UnterminatedStringFixer()
    
    print("🔧 Starting unterminated string literal fixes...")
    fixer.process_directory(root_path)
    fixer.print_summary()

if __name__ == '__main__':
    main()