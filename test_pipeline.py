#!/usr / bin / env python3
"""
Pipeline Debug Test
Simple test to verify CI / CD pipeline functionality
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def test_environment():
    """Test basic environment setup"""
    print("🔍 Testing environment setup...")

    # Check Python version
    python_version = sys.version_info
    print(
        f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}"
    )

    # Check current directory
    cwd = os.getcwd()
    print(f"✅ Current directory: {cwd}")

    # Check if this is a git repository
    try:
        result = subprocess.run(
            ["git", "rev - parse", "--git - dir"],
                capture_output = True,
                text = True,
                check = True,
                )
        print(f"✅ Git repository: {result.stdout.strip()}")
    except subprocess.CalledProcessError:
        print("❌ Not a git repository")
        return False

    return True


def test_required_files():
    """Test that required files exist"""
    print("\n📁 Testing required files...")

    required_files = [
        "requirements.txt",
            "main.py",
            ".github / workflows / ci - cd.yml",
            ".github / workflows / deploy.yml",
            ]

    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            all_exist = False

    return all_exist


def test_workflow_syntax():
    """Test GitHub Actions workflow syntax"""
    print("\n⚙️ Testing workflow syntax...")

    workflow_files = [
        ".github / workflows / ci - cd.yml",
            ".github / workflows / deploy.yml",
            ".github / workflows / ci.yml",
            ]

    for workflow in workflow_files:
        if Path(workflow).exists():
            try:
                with open(workflow, "r") as f:
                    content = f.read()
                    if "name:" in content and "on:" in content and "jobs:" in content:
                        print(f"✅ {workflow} - Valid structure")
                    else:
                        print(f"❌ {workflow} - Invalid structure")
                        return False
            except Exception as e:
                print(f"❌ {workflow} - Error reading: {e}")
                return False
        else:
            print(f"⚠️ {workflow} - Not found")

    return True


def test_dependencies():
    """Test that dependencies can be imported"""
    print("\n📦 Testing dependencies...")

    try:
        import fastapi

        print(f"✅ FastAPI: {fastapi.__version__}")
    except ImportError:
        print("❌ FastAPI not available")
        return False

    try:
        import uvicorn

        print(f"✅ Uvicorn: {uvicorn.__version__}")
    except ImportError:
        print("❌ Uvicorn not available")
        return False

    return True


def generate_pipeline_report():
    """Generate a pipeline debug report"""
    print("\n📊 Generating pipeline debug report...")

    report = {
        "timestamp": subprocess.run(
            ["date"], capture_output = True, text = True
        ).stdout.strip(),
            "environment": {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                "working_directory": os.getcwd(),
                "platform": sys.platform,
                },
            "git_status": {},
            "files_check": {},
            "dependencies": {},
            }

    # Git status
    try:
        branch = subprocess.run(
            ["git", "branch", "--show - current"],
                capture_output = True,
                text = True,
                check = True,
                )
        report["git_status"]["current_branch"] = branch.stdout.strip()

        commit = subprocess.run(
            ["git", "rev - parse", "HEAD"], capture_output = True, text = True, check = True
        )
        report["git_status"]["latest_commit"] = commit.stdout.strip()[:8]

        status = subprocess.run(
            ["git", "status", "--porcelain"], capture_output = True, text = True, check = True
        )
        report["git_status"]["uncommitted_changes"] = (
            len(status.stdout.strip().split("\n")) if status.stdout.strip() else 0
        )

    except subprocess.CalledProcessError as e:
        report["git_status"]["error"] = str(e)

    # Save report
    with open("pipeline_debug_report.json", "w") as f:
        json.dump(report, f, indent = 2)

    print(f"✅ Report saved to: pipeline_debug_report.json")
    return report


def main():
    """Main pipeline debug function"""
    print("🚀 TRAE AI Pipeline Debug Test")
    print("=" * 40)

    tests = [
        ("Environment Setup", test_environment),
            ("Required Files", test_required_files),
            ("Workflow Syntax", test_workflow_syntax),
            ("Dependencies", test_dependencies),
            ]

    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {e}")
            results.append((test_name, False))

    # Generate report
    report = generate_pipeline_report()

    # Summary
    print("\n" + "=" * 40)
    print("📋 PIPELINE DEBUG SUMMARY")
    print("=" * 40)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")

    print(f"\n🎯 Overall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Pipeline is ready for CI / CD!")
        return 0
    else:
        print("🔧 Pipeline needs fixes before CI / CD can work properly")
        return 1

if __name__ == "__main__":
    sys.exit(main())
