#!/usr / bin / env python3

import os
import re
import sys
from pathlib import Path


def fix_url_spaces(root_dir):
    """Fix URLs and API endpoints with spaces around slashes."""
    fixed_count = 0
    error_count = 0

    # Pattern to match URLs with spaces around slashes
    url_pattern = re.compile(r"(https?://[^\\s]*?)\\s+/\\s+([^\\s]*)", re.IGNORECASE)

    # Find all relevant files (Python, JavaScript, HTML, etc.)
    file_extensions = [
        ".py",
        ".js",
        ".html",
        ".json",
        ".md",
        ".txt",
        ".yml",
        ".yaml",
        ".sh",
# BRACKET_SURGEON: disabled
#     ]
    files_to_check = []

    for root, dirs, files in os.walk(root_dir):
        # Skip virtual environments and node_modules
        if "venv" in root or "node_modules" in root or ".git" in root:
            continue

        for file in files:
            if any(file.endswith(ext) for ext in file_extensions):
                files_to_check.append(os.path.join(root, file))

    print(f"Found {len(files_to_check)} files to check...")

    for file_path in files_to_check:
        try:
            # Try different encodings
            content = None
            encoding_used = None

            for encoding in ["utf - 8", "latin - 1", "cp1252"]:
                try:
                    with open(file_path, "r", encoding=encoding) as f:
                        content = f.read()
                    encoding_used = encoding
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                print(f"ERROR: Could not read {file_path} with any encoding")
                error_count += 1
                continue

            # Check if file has URLs with spaces
            if url_pattern.search(content):
                # Fix the URLs
                new_content = url_pattern.sub(r"\\1/\\2", content)

                # Write back with the same encoding
                with open(file_path, "w", encoding=encoding_used) as f:
                    f.write(new_content)

                print(f"FIXED: {file_path}")
                fixed_count += 1

        except Exception as e:
            print(f"ERROR processing {file_path}: {e}")
            error_count += 1

    print(f"\\nSummary:")
    print(f"Files fixed: {fixed_count}")
    print(f"Errors encountered: {error_count}")
    return fixed_count, error_count


if __name__ == "__main__":
    root_directory = "/Users / thomasbrianreynolds / online production"
    if len(sys.argv) > 1:
        root_directory = sys.argv[1]

    print(f"Fixing URL spaces in: {root_directory}")
    fix_url_spaces(root_directory)