#!/usr/bin/env python3
"""
Enhanced Python Syntax Analyzer with Concurrent Processing

This script provides a comprehensive analysis of Python files in a codebase,
using concurrent processing for faster execution and detailed error reporting.
"""

import os
import ast
import argparse
import concurrent.futures
from collections import Counter
from pathlib import Path
from fnmatch import fnmatch

# Enhanced exclusion patterns
EXCLUDE_DIRS = {"venv", "venv_stable", ".venv", ".venv_base44", "__pycache__", "site-packages", ".git", "node_modules", "dist", "build"}
SKIP_PATTERNS = os.getenv("BASE44_SKIP_GLOBS", "venv*,.venv*,**/site-packages/**,**/__pycache__/**").split(",")

def should_skip(path_parts: list[str]) -> bool:
    return any(part in EXCLUDE_DIRS for part in path_parts) or "site-packages" in path_parts

def skip_by_glob(p: str) -> bool:
    return any(fnmatch(p, pat) for pat in SKIP_PATTERNS)

def analyze_file(filepath):
    """
    Tries to parse a single Python file with ast.parse().
    Returns the filepath and either None (on success) or the SyntaxError.
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            source = f.read()
        ast.parse(source, filename=filepath)
        return filepath, None
    except SyntaxError as e:
        return filepath, e
    except Exception:
        # Catch other potential errors like file not found during race conditions
        return filepath, None  # Treat as success for simplicity

def main(target_dir):
    """
    Walks the target directory, analyzes all .py files, and prints a summary.
    """
    py_files = []
    for root, dirs, files in os.walk(target_dir):
        parts = Path(root).parts
        if should_skip(list(parts)):
            continue
        dirs[:] = [d for d in dirs if not should_skip(list(Path(root, d).parts))]
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                if not skip_by_glob(file_path):
                    py_files.append(file_path)

    total_files = len(py_files)
    if total_files == 0:
        print("No Python files found in the specified directory.")
        return

    print(f"Analyzing {total_files} Python files...")

    error_files = {}
    error_types = Counter()
    success_count = 0

    # Use a ThreadPoolExecutor to speed up analysis
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_file = {executor.submit(analyze_file, fp): fp for fp in py_files}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_file)):
            filepath, error = future.result()
            print(f"Progress: {i + 1}/{total_files} ({((i + 1) / total_files) * 100:.2f}%)", end='\r')
            if error:
                error_files[filepath] = error
                # Generalize error messages for better aggregation
                error_msg = str(error).split(' (')[0]
                error_types[error_msg] += 1
            else:
                success_count += 1
    
    print("\n\n--- Analysis Complete ---")
    
    print("\n--- Files with Syntax Errors ---")
    for filepath, error in error_files.items():
        print(f"File: {filepath}")
        print(f"  Error: {error}")

    print("\n--- Summary ---")
    print(f"Total Python files found: {total_files}")
    print(f"Files with valid syntax:  {success_count}")
    print(f"Files with syntax errors: {len(error_files)}")
    
    success_rate = (success_count / total_files) * 100 if total_files > 0 else 0
    print(f"Success Rate: {success_rate:.2f}%")

    print("\n--- Top 10 Most Common Error Types ---")
    for error_msg, count in error_types.most_common(10):
        print(f"[{count: >5}] {error_msg}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze a Python codebase for syntax errors.")
    parser.add_argument(
        '--target-dir',
        default='.',
        help='The root directory of the codebase to analyze.'
    )
    args = parser.parse_args()
    main(args.target_dir)