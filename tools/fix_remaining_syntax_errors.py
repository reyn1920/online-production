#!/usr/bin/env python3
"""
Enhanced syntax error fixer for remaining edge cases.
Handles complex docstring patterns and syntax issues not caught by the initial fixer.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple


class EnhancedSyntaxFixer:
    """Enhanced tool to fix remaining syntax errors."""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.fixed_files = []
        self.error_files = []
        self.stats = {
            'files_processed': 0,
            'files_fixed': 0,
            'issues_fixed': 0,
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
    
    def fix_docstring_issues(self, content: str) -> Tuple[str, int]:
        """Fix various docstring-related syntax issues."""
        fixes_count = 0
        original_content = content
        
        # Fix 1: Standalone docstrings that should be comments
        # Pattern: """Some text""" on its own line (not after def/class)
        lines = content.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            # Check if this is a standalone docstring
            stripped = line.strip()
            if (stripped.startswith('"""') and stripped.endswith('"""') and 
                len(stripped) > 6 and '"""' not in stripped[3:-3]):
                
                # Check if previous line is a function/class definition
                prev_line = lines[i-1].strip() if i > 0 else ""
                if not (prev_line.endswith(':') and ('def ' in prev_line or 'class ' in prev_line)):
                    # This is likely a standalone docstring, convert to comment
                    comment_text = stripped[3:-3].strip()
                    fixed_lines.append(f"{line[:len(line)-len(stripped)]}# {comment_text}")
                    fixes_count += 1
                    continue
            
            fixed_lines.append(line)
        
        content = '\n'.join(fixed_lines)
        
        # Fix 2: Unterminated triple-quoted strings
        # Look for """ that don't have matching closing """
        triple_quote_pattern = r'"""[^"]*?(?:"(?!"")|[^"]*)*?(?:"""|
\s*$)'
        matches = list(re.finditer(r'"""', content))
        
        # Count opening vs closing triple quotes
        if len(matches) % 2 != 0:
            # Odd number of triple quotes - likely unterminated
            # Find the last one and add closing quotes
            last_match = matches[-1]
            end_pos = last_match.end()
            
            # Look for the end of the logical block
            remaining = content[end_pos:]
            lines_after = remaining.split('\n')
            
            # Find where to insert the closing quotes
            insert_pos = end_pos
            for j, line_after in enumerate(lines_after):
                if line_after.strip() and not line_after.startswith(' '):
                    # Found start of next block
                    insert_pos = end_pos + sum(len(l) + 1 for l in lines_after[:j])
                    break
            
            # Insert closing quotes
            content = content[:insert_pos] + '\n"""\n' + content[insert_pos:]
            fixes_count += 1
        
        # Fix 3: Invalid syntax in docstrings (like bare expressions)
        # Replace problematic patterns
        problematic_patterns = [
            (r'"""Update endpoint health in database"""\s*\n\s*\^+', '"""Update endpoint health in database"""'),
            (r'"""[^"]*?"""\s*\n\s*\^+', lambda m: m.group(0).split('\n')[0]),
        ]
        
        for pattern, replacement in problematic_patterns:
            if callable(replacement):
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            else:
                old_content = content
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
                if content != old_content:
                    fixes_count += 1
        
        return content, fixes_count
    
    def fix_method_signature_issues(self, content: str) -> Tuple[str, int]:
        """Fix method signature syntax issues."""
        fixes_count = 0
        
        # Fix incomplete method signatures
        # Pattern: method definition that spans multiple lines incorrectly
        pattern = r'(def\s+\w+\([^)]*?)\n\s*(self,\s*[^)]+)\)\s*->'
        matches = re.finditer(pattern, content, re.MULTILINE)
        
        for match in matches:
            old_text = match.group(0)
            # Combine the signature into one line
            new_text = f"{match.group(1)}, {match.group(2).strip()}) ->"
            content = content.replace(old_text, new_text)
            fixes_count += 1
        
        return content, fixes_count
    
    def process_file(self, file_path: Path) -> bool:
        """Process a single Python file to fix syntax issues."""
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Apply fixes
            content = original_content
            total_fixes = 0
            
            # Fix docstring issues
            content, docstring_fixes = self.fix_docstring_issues(content)
            total_fixes += docstring_fixes
            
            # Fix method signature issues
            content, signature_fixes = self.fix_method_signature_issues(content)
            total_fixes += signature_fixes
            
            # Write back if changes were made
            if total_fixes > 0:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.fixed_files.append(str(file_path))
                self.stats['files_fixed'] += 1
                self.stats['issues_fixed'] += total_fixes
                
                print(f"✓ Fixed {total_fixes} issue(s) in {file_path.relative_to(self.root_dir)}")
            
            self.stats['files_processed'] += 1
            return True
            
        except Exception as e:
            self.error_files.append((str(file_path), str(e)))
            self.stats['errors'] += 1
            print(f"✗ Error processing {file_path.relative_to(self.root_dir)}: {e}")
            return False
    
    def run(self) -> None:
        """Execute the enhanced syntax fixing process."""
        print("🔧 Starting enhanced syntax error fix process...")
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
        print("📊 ENHANCED SYNTAX FIX SUMMARY")
        print("="*60)
        print(f"Files processed: {self.stats['files_processed']}")
        print(f"Files fixed: {self.stats['files_fixed']}")
        print(f"Total issues fixed: {self.stats['issues_fixed']}")
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
        
        print("\n🎉 Enhanced syntax fix process completed!")


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        root_dir = sys.argv[1]
    else:
        root_dir = os.getcwd()
    
    fixer = EnhancedSyntaxFixer(root_dir)
    fixer.run()


if __name__ == '__main__':
    main()