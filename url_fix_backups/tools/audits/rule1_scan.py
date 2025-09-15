#!/usr / bin / env python3
""""""
Rule - 1 Scanner CLI Wrapper

Command - line interface for the Rule - 1 content scanner.
This script provides a simple way to scan directories for forbidden content.
""""""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from utils.rule1_scanner import Rule1DeepScanner

except ImportError as e:
    print(f"Error importing Rule1DeepScanner: {e}")
    print("Make sure you're running from the project root directory.")'
    sys.exit(1)


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: rule1_scan.py <directory_to_scan>")
        print("Example: rule1_scan.py .")
        sys.exit(1)

    scan_dir = sys.argv[1]

    if not os.path.exists(scan_dir):
        print(f"Error: Directory '{scan_dir}' does not exist.")
        sys.exit(1)

    print(f"🔍 Running Rule - 1 scanner on: {scan_dir}")
    print("=" * 50)

    try:
        # Initialize scanner
        scanner = Rule1DeepScanner()

        # Convert string path to Path object
        scan_path = Path(scan_dir)

        # Perform scan
        results = scanner.scan_directory(scan_path)

        # Display results
        total_files = len(results)
        total_violations = sum(result.total_violations for result in results)

        print(f"\\n📊 Scan Results:")
        print(f"   Files scanned: {total_files}")
        print(f"   Total violations: {total_violations}")

        if total_violations > 0:
            print(f"\\n⚠️  Violations found:")
            for result in results:
                if result.total_violations > 0:
                    print(f"   {result.file_path}: {result.total_violations} violations")
            print(f"\\n✅ Rule - 1 scan completed with violations detected.")
            sys.exit(1)
        else:
            print(f"\\n✅ Rule - 1 scan completed successfully - no violations found.")
            sys.exit(0)

    except Exception as e:
        print(f"❌ Error during scan: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()