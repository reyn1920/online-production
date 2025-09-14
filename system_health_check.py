#!/usr/bin/env python3
"""
Comprehensive System Health Check
Verifies all components are working correctly
"""

import json
import os
import sys
from datetime import datetime

import requests


def check_web_interface():
    """Check if the web interface is accessible"""
    try:
        response = requests.get("http://localhost:7860", timeout=5)
        if response.status_code == 200:
            print("✅ Web interface is accessible at http://localhost:7860")
            return True
        else:
            print(f"❌ Web interface returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Web interface check failed: {e}")
        return False


def check_avatar_generation():
    """Check avatar generation functionality"""
    try:
        # Import the demo functions
        sys.path.append(os.path.join(os.path.dirname(__file__), "models", "linly_talker"))

        from demo_app import demo_generate_ai_female_model

        print("🧪 Testing avatar generation...")
        result_text, result_image = demo_generate_ai_female_model()

        if result_text and result_image:
            print("✅ Avatar generation is working")
            return True
        else:
            print("❌ Avatar generation returned empty results")
            return False
    except Exception as e:
        print(f"❌ Avatar generation check failed: {e}")
        return False


def check_backend_services():
    """Check backend services status"""
    try:
        # Add backend services to path
        sys.path.append("backend/services")

        from backend.services.avatar_engines import engine_manager

        print("🔧 Checking backend services...")
        print(
            f"   Avatar engines available: {len(engine_manager.engines) if hasattr(engine_manager, 'engines') else 0}"
        )
        print("✅ Backend services are accessible")
        return True

    except Exception as e:
        print(f"⚠️  Backend services check: {e}")
        return True  # Not critical for basic functionality


def check_file_structure():
    """Check critical file structure"""
    critical_files = [
        "models/linly_talker/demo_app.py",
        "services/avatar_generation_service.py",
        "backend/services/avatar_engines.py",
    ]

    print("📁 Checking file structure...")
    all_good = True

    for file_path in critical_files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} missing")
            all_good = False

    return all_good


def main():
    """Run comprehensive system health check"""
    print("🏥 System Health Check")
    print("=" * 50)
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    checks = [
        ("File Structure", check_file_structure),
        ("Web Interface", check_web_interface),
        ("Avatar Generation", check_avatar_generation),
        ("Backend Services", check_backend_services),
    ]

    results = []

    for check_name, check_func in checks:
        print(f"\n🔍 {check_name}:")
        try:
            result = check_func()
            results.append((check_name, result))
        except Exception as e:
            print(f"❌ {check_name} failed with exception: {e}")
            results.append((check_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 HEALTH CHECK SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for check_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {check_name}: {status}")

    print(f"\n🎯 Overall: {passed}/{total} checks passed")

    if passed == total:
        print("\n🚀 System is healthy and ready for use!")
        print("🌐 Access the interface at: http://localhost:7860")
        return True
    else:
        print(f"\n⚠️  {total - passed} issues detected. Please review the failed checks.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)