#!/usr/bin/env python3
import ast
import sys

try:
    with open('backend/app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Try to parse the entire file
    ast.parse(content)
    print("✅ File parses successfully!")
    
except SyntaxError as e:
    print(f"❌ Syntax Error at line {e.lineno}:")
    print(f"Text: {repr(e.text)}")
    print(f"Error: {e.msg}")
    
    # Show context around the error
    lines = content.split('\n')
    start = max(0, e.lineno - 3)
    end = min(len(lines), e.lineno + 2)
    
    print("\nContext:")
    for i in range(start, end):
        marker = ">>> " if i + 1 == e.lineno else "    "
        print(f"{marker}{i+1:4d}: {lines[i]}")
        
except Exception as e:
    print(f"❌ Other error: {e}")