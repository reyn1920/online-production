#!/usr / bin / env python3
"""
Submit paste content to the paste app running on localhost:8080
"""

import json

import requests


def submit_paste_content():
    # Read the full paste content
    with open(
        "/Users / thomasbrianreynolds / online production / paste_content.txt", "r"
    ) as f:
        content = f.read()

    # Since the paste app doesn't have an API endpoint, let's create a simple submission
    # by directly accessing the web interface and simulating the form submission

    print(f"Content length: {len(content)} characters")
    print(f"Content preview (first 200 chars): {content[:200]}...")

    # For now, let's just display the content since the paste app only has a client - side interface
    print("\n=== PASTE CONTENT (Lines 1 - 881) ===")
    print(content)
    print("\n=== END OF PASTE CONTENT ===")

    print("\nNote: The paste app at localhost:8080 only has a client - side interface.")
    print("To submit this content, you would need to:")
    print("1. Open http://localhost:8080 in a browser")
    print("2. Copy and paste the content into the textarea")
    print("3. Click 'Save Paste'")

    return True

if __name__ == "__main__":
    submit_paste_content()
