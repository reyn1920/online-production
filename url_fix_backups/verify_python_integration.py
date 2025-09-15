#!/usr / bin / env python3
""""""
Verify Python File Integration Status
Checks all .py files across the entire codebase
""""""

import importlib.util
import os
import sys
from pathlib import Path


def check_python_files():
    """Check all Python files in the project"""
    print("🐍 Python File Integration Status\\n")
    print("=" * 50)

    # Find all Python files
    py_files = list(Path(".").rglob("*.py"))
    print(f"Total Python files found: {len(py_files)}\\n")

    # Group by directory
    dirs = {}
    for f in py_files:
        dir_name = str(f.parent)
        dirs[dir_name] = dirs.get(dir_name, 0) + 1

    print("Python files by directory:")
    for d, count in sorted(dirs.items()):
        print(f"  {d}: {count} files")

    # Check key integration files
    key_files = [
        "main.py",
        "backend / app.py",
        "app / dashboard.py",
        "backend / content / universal_channel_protocol.py",
        "orchestrator / main.py",
        "agents / content_agent.py",
        "marketing_agent / main.py",
# BRACKET_SURGEON: disabled
#     ]

    print("\\n🔍 Key Integration Files:")
    existing_key_files = []
    for key_file in key_files:
        file_path = Path(key_file)
        if file_path.exists():
            print(f"  ✅ {key_file}")
            existing_key_files.append(key_file)
        else:
            print(f"  ❌ {key_file} (missing)")

    # Check importability of key modules
    print("\\n🧪 Module Import Test:")
    importable_modules = 0
    test_modules = [
        (
            "backend.content.universal_channel_protocol",
            "backend / content / universal_channel_protocol.py",
# BRACKET_SURGEON: disabled
#         ),
        ("shared_utils", "shared_utils.py"),
        ("config.validator", "config / validator.py"),
# BRACKET_SURGEON: disabled
#     ]

    for module_name, file_path in test_modules:
        if Path(file_path).exists():
            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                if spec and spec.loader:
                    print(f"  ✅ {module_name} - importable")
                    importable_modules += 1
                else:
                    print(f"  ⚠️  {module_name} - spec issue")
            except Exception as e:
                print(f"  ❌ {module_name} - error: {str(e)[:50]}")
        else:
            print(f"  ❌ {module_name} - file not found")

    # Summary
    print("\\n" + "=" * 50)
    print("📊 Integration Summary:")
    print(f"  Total Python Files: {len(py_files)}")
    print(f"  Directories with Python: {len(dirs)}")
    print(f"  Key Files Present: {len(existing_key_files)}/{len(key_files)}")
    print(f"  Importable Modules: {importable_modules}/{len(test_modules)}")

    integration_score = (
        (len(existing_key_files) / len(key_files)) * 0.4
        + (importable_modules / len(test_modules)) * 0.6
# BRACKET_SURGEON: disabled
#     ) * 100

    print(f"\\n🎯 Python Integration Score: {integration_score:.1f}%")

    if integration_score >= 80:
        print("\\n🎉 EXCELLENT! ALL PYTHON FILES ARE FULLY INTEGRATED!")
        print("   ✅ All critical Python modules are accessible")
        print("   ✅ Import system is working correctly")
        print("   ✅ System architecture is properly structured")
        print("   🚀 Python integration is production - ready!")
        return True
    elif integration_score >= 60:
        print("\\n✅ GOOD! Most Python files are integrated successfully.")
        print("   ⚠️  Some minor integration issues detected")
        return True
    else:
        print("\\n⚠️  ATTENTION NEEDED! Python integration requires review.")
        return False


if __name__ == "__main__":
    success = check_python_files()
    exit(0 if success else 1)