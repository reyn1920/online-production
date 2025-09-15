#!/usr/bin/env python3
"""
Automated script to fix empty docstring patterns across the backend codebase.
This script addresses the systematic issue of malformed docstrings ("""""") 
that cause syntax errors in Python files.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


class DocstringFixer:
    """Professional-grade tool to fix malformed docstring patterns."""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.fixed_files = []
        self.error_files = []
        self.stats = {
            'files_processed': 0,
            'files_fixed': 0,
            'docstrings_fixed': 0,
            'errors': 0
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
    
    def fix_empty_docstrings(self, content: str) -> Tuple[str, int]:
        """Fix empty docstring patterns in file content."""
        fixes_count = 0
        
        # Pattern 1: Fix standalone empty docstrings """"""
        pattern1 = r'""""""'
        matches1 = re.findall(pattern1, content)
        if matches1:
            content = re.sub(pattern1, '""""""', content)
            fixes_count += len(matches1)
        
        # Pattern 2: Fix SQL statements with empty docstrings
        # Look for conn.execute("""""" followed by SQL keywords
        pattern2 = r'conn\.execute\(""""""\s*(CREATE|SELECT|INSERT|UPDATE|DELETE|DROP)'
        matches2 = re.finditer(pattern2, content, re.IGNORECASE | re.MULTILINE)
        for match in matches2:
            # Replace the empty docstring with proper triple quotes
            old_text = match.group(0)
            new_text = old_text.replace('""""""', '"""')
            content = content.replace(old_text, new_text)
            fixes_count += 1
        
        # Pattern 3: Fix general empty docstrings at start of functions/classes
        pattern3 = r'^(\s*)(def|class)([^:]+:)\s*\n\s*""""""'
        matches3 = re.finditer(pattern3, content, re.MULTILINE)
        for match in matches3:
            old_text = match.group(0)
            new_text = old_text.replace('""""""', '"""\n    TODO: Add documentation\n    """')
            content = content.replace(old_text, new_text)
            fixes_count += 1
        
        return content, fixes_count
    
    def process_file(self, file_path: Path) -> bool:
        """Process a single Python file to fix docstring issues."""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Fix docstring issues
            fixed_content, fixes_count = self.fix_empty_docstrings(original_content)
            
            # Write back if changes were made
            if fixes_count > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                self.fixed_files.append(str(file_path))
                self.stats['files_fixed'] += 1
                self.stats['docstrings_fixed'] += fixes_count
                
                print(f"✓ Fixed {fixes_count} docstring(s) in {file_path.relative_to(self.root_dir)}")
            
            self.stats['files_processed'] += 1
            return True
            
        except Exception as e:
            self.error_files.append((str(file_path), str(e)))
            self.stats['errors'] += 1
            print(f"✗ Error processing {file_path.relative_to(self.root_dir)}: {e}")
            return False
    
    def run(self) -> None:
        """Execute the docstring fixing process."""
        print("🔧 Starting automated docstring fix process...")
        print(f"📁 Scanning directory: {self.root_dir}")
        
        # Find all Python files
        python_files = self.find_python_files()
        if not python_files:
            print("❌ No Python files found in backend directory")
            return
        
        print(f"📄 Found {len(python_files)} Python files to process")
        
        # Process each file
        for file_path in python_files:
            self.process_file(file_path)
        
        # Print summary
        self.print_summary()
    
    def print_summary(self) -> None:
        """Print processing summary."""
        print("\n" + "="*60)
        print("📊 DOCSTRING FIX SUMMARY")
        print("="*60)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files fixed: {self.stats['files_fixed']}")
        print(f"Total docstrings fixed: {self.stats['docstrings_fixed']}")
        print(f"Errors encountered: {self.stats['errors']}")
        
        if self.fixed_files:
            print("\n✅ Successfully fixed files:")
            for file_path in self.fixed_files[:10]:  # Show first 10
                print(f"  • {file_path}")
            if len(self.fixed_files) > 10:
                print(f"  ... and {len(self.fixed_files) - 10} more files")
        
        if self.error_files:
            print("\n❌ Files with errors:")
            for file_path, error in self.error_files:
                print(f"  • {file_path}: {error}")
        
        print("\n🎉 Docstring fix process completed!")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = os.getcwd()
    
    fixer = DocstringFixer(root_dir)
    fixer.run()


if __name__ == '__main__':
    main()