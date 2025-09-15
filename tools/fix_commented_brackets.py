#!/usr/bin/env python3
"""
Automated script to fix commented closing brackets across the backend codebase.
This script addresses the systematic issue of commented-out closing brackets 
with 'FIXIT: commented possible stray closer' comments.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict


class BracketFixer:
    """Professional-grade tool to fix commented closing bracket patterns."""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.fixed_files = []
        self.error_files = []
        self.stats = {
            'files_processed': 0,
            'files_fixed': 0,
            'brackets_fixed': 0,
            'errors': 0
        }
        self.bracket_patterns = {
            'parentheses': r'#\s*\)\s*#\s*FIXIT:?\s*commented\s*possible\s*stray\s*closer',
            'square_brackets': r'#\s*\]\s*#\s*FIXIT:?\s*commented\s*possible\s*stray\s*closer',
            'curly_braces': r'#\s*\}\s*#\s*FIXIT:?\s*commented\s*possible\s*stray\s*closer'
        }
    
    def find_python_files(self) -> List[Path]:
        """Find all Python files in the backend directory."""
        backend_dir = self.root_dir / 'backend'
        if not backend_dir.exists():
            print(f"Error: Backend directory not found at {backend_dir}")
            return []
        
        python_files = []
        for file_path in backend_dir.rglob('*.py'):
            if file_path.is_file():
                python_files.append(file_path)
        
        return python_files
    
    def analyze_bracket_balance(self, content: str) -> Dict[str, int]:
        """Analyze bracket balance in the content."""
        balance = {'(': 0, '[': 0, '{': 0}
        
        # Count brackets, ignoring those in strings and comments
        in_string = False
        in_comment = False
        string_char = None
        
        i = 0
        while i < len(content):
            char = content[i]
            
            # Handle string literals
            if char in ['"', "'"] and not in_comment:
                if not in_string:
                    in_string = True
                    string_char = char
                elif char == string_char and (i == 0 or content[i-1] != '\\'):
                    in_string = False
                    string_char = None
            
            # Handle comments
            elif char == '#' and not in_string:
                in_comment = True
            elif char == '\n':
                in_comment = False
            
            # Count brackets outside strings and comments
            elif not in_string and not in_comment:
                if char == '(':
                    balance['('] += 1
                elif char == ')':
                    balance['('] -= 1
                elif char == '[':
                    balance['['] += 1
                elif char == ']':
                    balance['['] -= 1
                elif char == '{':
                    balance['{'] += 1
                elif char == '}':
                    balance['{'] -= 1
            
            i += 1
        
        return balance
    
    def fix_commented_brackets(self, content: str) -> Tuple[str, int]:
        """Fix commented closing brackets in file content."""
        fixes_count = 0
        lines = content.split('\n')
        fixed_lines = []
        
        for line_num, line in enumerate(lines):
            original_line = line
            
            # Check for each bracket pattern
            for bracket_type, pattern in self.bracket_patterns.items():
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    # Extract the bracket character
                    if bracket_type == 'parentheses':
                        bracket = ')'
                    elif bracket_type == 'square_brackets':
                        bracket = ']'
                    else:  # curly_braces
                        bracket = '}'
                    
                    # Replace the commented bracket with uncommented version
                    # Remove the entire FIXIT comment and uncomment the bracket
                    line = re.sub(pattern, bracket, line, flags=re.IGNORECASE)
                    fixes_count += 1
                    
                    print(f"  Line {line_num + 1}: Uncommented {bracket}")
            
            fixed_lines.append(line)
        
        return '\n'.join(fixed_lines), fixes_count
    
    def validate_syntax_after_fix(self, content: str, file_path: Path) -> bool:
        """Validate that the fixed content has balanced brackets."""
        try:
            balance = self.analyze_bracket_balance(content)
            
            # Check if brackets are balanced
            unbalanced = []
            for bracket, count in balance.items():
                if count != 0:
                    bracket_name = {'(': 'parentheses', '[': 'square brackets', '{': 'curly braces'}[bracket]
                    unbalanced.append(f"{bracket_name}: {count}")
            
            if unbalanced:
                print(f"  ⚠️  Warning: Unbalanced brackets in {file_path.name}: {', '.join(unbalanced)}")
                return False
            
            return True
            
        except Exception as e:
            print(f"  ⚠️  Warning: Could not validate syntax for {file_path.name}: {e}")
            return False
    
    def process_file(self, file_path: Path) -> bool:
        """Process a single Python file to fix bracket issues."""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Check if file contains FIXIT comments
            if 'FIXIT' not in original_content:
                self.stats['files_processed'] += 1
                return True
            
            print(f"🔧 Processing {file_path.relative_to(self.root_dir)}...")
            
            # Fix bracket issues
            fixed_content, fixes_count = self.fix_commented_brackets(original_content)
            
            # Write back if changes were made
            if fixes_count > 0:
                # Validate syntax before writing
                if self.validate_syntax_after_fix(fixed_content, file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    
                    self.fixed_files.append(str(file_path))
                    self.stats['files_fixed'] += 1
                    self.stats['brackets_fixed'] += fixes_count
                    
                    print(f"✓ Fixed {fixes_count} bracket(s) in {file_path.relative_to(self.root_dir)}")
                else:
                    print(f"⚠️  Skipped {file_path.name} due to potential syntax issues")
            
            self.stats['files_processed'] += 1
            return True
            
        except Exception as e:
            self.error_files.append((str(file_path), str(e)))
            self.stats['errors'] += 1
            print(f"✗ Error processing {file_path.relative_to(self.root_dir)}: {e}")
            return False
    
    def run(self, dry_run: bool = False) -> None:
        """Execute the bracket fixing process."""
        mode = "DRY RUN" if dry_run else "LIVE FIX"
        print(f"🔧 Starting automated bracket fix process ({mode})...")
        print(f"📁 Scanning directory: {self.root_dir}")
        
        # Find all Python files
        python_files = self.find_python_files()
        if not python_files:
            print("❌ No Python files found in backend directory")
            return
        
        print(f"📄 Found {len(python_files)} Python files to process")
        
        # Process each file
        for file_path in python_files:
            if not dry_run:
                self.process_file(file_path)
            else:
                # In dry run, just check for FIXIT comments
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    if 'FIXIT' in content:
                        fixit_count = content.count('FIXIT')
                        print(f"📋 {file_path.relative_to(self.root_dir)}: {fixit_count} FIXIT comment(s)")
                        self.stats['files_processed'] += 1
                        self.stats['brackets_fixed'] += fixit_count
                except Exception as e:
                    print(f"✗ Error reading {file_path.relative_to(self.root_dir)}: {e}")
        
        # Print summary
        self.print_summary(dry_run)
    
    def print_summary(self, dry_run: bool = False) -> None:
        """Print processing summary."""
        mode = "DRY RUN" if dry_run else "LIVE FIX"
        print("\n" + "="*60)
        print(f"📊 BRACKET FIX SUMMARY ({mode})")
        print("="*60)
        print(f"Files processed: {self.stats['files_processed']}")
        if not dry_run:
            print(f"Files fixed: {self.stats['files_fixed']}")
        print(f"Total brackets {'found' if dry_run else 'fixed'}: {self.stats['brackets_fixed']}")
        print(f"Errors encountered: {self.stats['errors']}")
        
        if self.fixed_files and not dry_run:
            print("\n✅ Successfully fixed files:")
            for file_path in self.fixed_files[:10]:  # Show first 10
                print(f"  • {file_path}")
            if len(self.fixed_files) > 10:
                print(f"  ... and {len(self.fixed_files) - 10} more files")
        
        if self.error_files:
            print("\n❌ Files with errors:")
            for file_path, error in self.error_files:
                print(f"  • {file_path}: {error}")
        
        if dry_run:
            print("\n💡 Run without --dry-run to apply fixes")
        else:
            print("\n🎉 Bracket fix process completed!")


def main():
    """Main entry point."""
    dry_run = '--dry-run' in sys.argv
    
    if len(sys.argv) > 1 and sys.argv[1] != '--dry-run':
        root_dir = sys.argv[1]
    else:
        root_dir = os.getcwd()
    
    fixer = BracketFixer(root_dir)
    fixer.run(dry_run=dry_run)


if __name__ == '__main__':
    main()