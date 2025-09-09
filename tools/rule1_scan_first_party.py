#!/usr/bin/env python3
"""
Rule-1 First-Party Scanner

Optimized scanner that only processes first-party code files,
avoiding third-party dependencies and generated content.

Usage:
    python3 tools/rule1_scan_first_party.py                    # Preview files
    python3 tools/rule1_scan_first_party.py --print-files      # Print file paths
    python3 tools/rule1_scan_first_party.py --scan             # Actually scan
"""

import sys
import os
import json
from pathlib import Path
from typing import List, Set

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def load_ignore_patterns() -> Set[str]:
    """Load ignore patterns from .rule1_ignore file."""
    ignore_file = Path(".rule1_ignore")
    patterns = set()
    
    if ignore_file.exists():
        with open(ignore_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.add(line)
    
    return patterns

def should_ignore_path(path: Path, ignore_patterns: Set[str]) -> bool:
    """Check if a path should be ignored based on patterns."""
    path_str = str(path)
    
    for pattern in ignore_patterns:
        if pattern.endswith('/'):
            # Directory pattern
            if pattern[:-1] in path.parts:
                return True
        elif '*' in pattern:
            # Glob pattern - simple check
            if pattern.replace('*', '') in path_str:
                return True
        else:
            # Exact match or substring
            if pattern in path_str or path.name == pattern:
                return True
    
    return False

def get_first_party_files(root_dir: Path = None) -> List[Path]:
    """Get list of first-party files to scan."""
    if root_dir is None:
        root_dir = Path('.')
    
    ignore_patterns = load_ignore_patterns()
    first_party_files = []
    
    # File extensions to include
    include_extensions = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss',
        '.json', '.yaml', '.yml', '.md', '.txt', '.sql', '.sh', '.bash'
    }
    
    for file_path in root_dir.rglob('*'):
        if not file_path.is_file():
            continue
            
        # Skip if matches ignore patterns
        if should_ignore_path(file_path, ignore_patterns):
            continue
            
        # Only include specific file types
        if file_path.suffix.lower() not in include_extensions:
            continue
            
        # Skip very large files (likely not first-party)
        try:
            if file_path.stat().st_size > 1024 * 1024:  # 1MB limit
                continue
        except OSError:
            continue
            
        first_party_files.append(file_path)
    
    return sorted(first_party_files)

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Rule-1 First-Party Scanner')
    parser.add_argument('--print-files', action='store_true',
                       help='Print file paths only (for piping to scanner)')
    parser.add_argument('--scan', action='store_true',
                       help='Actually run the scanner on first-party files')
    parser.add_argument('--limit', type=int, default=50,
                       help='Limit number of files to show in preview (default: 50)')
    
    args = parser.parse_args()
    
    # Get first-party files
    files = get_first_party_files()
    
    if args.print_files:
        # Print file paths for piping to scanner
        for file_path in files:
            print(str(file_path))
        return
    
    if args.scan:
        # Actually run the scanner
        try:
            from utils.rule1_scanner import Rule1DeepScanner
            
            print(f"🔍 Scanning {len(files)} first-party files...")
            scanner = Rule1DeepScanner()
            
            total_violations = 0
            files_with_violations = 0
            
            for file_path in files:
                try:
                    result = scanner.scan_file(file_path)
                    if result.total_violations > 0:
                        files_with_violations += 1
                        total_violations += result.total_violations
                        print(f"⚠️  {file_path}: {result.total_violations} violations")
                except Exception as e:
                    print(f"❌ Error scanning {file_path}: {e}")
            
            print(f"\n📊 Scan Results:")
            print(f"   Files scanned: {len(files)}")
            print(f"   Files with violations: {files_with_violations}")
            print(f"   Total violations: {total_violations}")
            
            if total_violations > 0:
                print(f"\n⚠️  Rule-1 violations found in first-party code.")
                sys.exit(1)
            else:
                print(f"\n✅ No Rule-1 violations found in first-party code.")
                sys.exit(0)
                
        except ImportError as e:
            print(f"❌ Error importing scanner: {e}")
            sys.exit(1)
    else:
        # Preview mode (default)
        print(f"📋 First-party files to scan ({len(files)} total):")
        print("=" * 50)
        
        # Show first N files as JSON for easy parsing
        preview_files = files[:args.limit]
        file_list = [str(f) for f in preview_files]
        
        print(json.dumps(file_list, indent=2))
        
        if len(files) > args.limit:
            print(f"\n... and {len(files) - args.limit} more files")
        
        print(f"\n💡 Use --scan to actually run the scanner")
        print(f"💡 Use --print-files to get paths for piping")

if __name__ == '__main__':
    main()
