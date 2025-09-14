#!/usr/bin/env python3
"""
Debug script to isolate BreakingNewsWatcher initialization issues.
"""

import logging
import os
import sys

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.DEBUG)

print("Starting BreakingNewsWatcher debug...")

try:
    print("Importing BreakingNewsWatcher...")

    from backend.agents.research_tools import BreakingNewsWatcher

    print("Import successful!")

    print("Creating BreakingNewsWatcher instance...")
    news_watcher = BreakingNewsWatcher()
    print("Instance created successfully!")

    print("Checking logger attribute...")
    if hasattr(news_watcher, "logger"):
        print(f"Logger found: {news_watcher.logger}")
    else:
        print("ERROR: Logger attribute not found!")

    print("Checking other attributes...")
    print(f"Feeds: {len(news_watcher.feeds) if hasattr(news_watcher, 'feeds') else 'Not found'}")
    print(f"Config: {news_watcher.config if hasattr(news_watcher, 'config') else 'Not found'}")

except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

    import traceback

    traceback.print_exc()

print("Debug complete.")
