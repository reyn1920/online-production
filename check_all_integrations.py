#!/usr/bin/env python3
""""""
Check All System Integrations Status
Verifies that all folders and components are properly integrated
""""""

from pathlib import Path

import requests

from backend.content.universal_channel_protocol import get_protocol


def check_software_integrations():
    """Check system software integrations"""
    try:
        print("🔍 Checking Software Integrations...")
        response = requests.get("http://localhost:8000/system - software/status")

        if response.status_code == 200:
            data = response.json()
            total = data.get("total_software", 0)
            available = data.get("available_count", 0)

            print(f"  Total Software: {total}")
            print(f"  Available: {available}")
            print(
                f"  Integration Rate: {(available/total * 100):.1f}%"
                if total > 0
                else "  Integration Rate: 0%"
# BRACKET_SURGEON: disabled
#             )

            # Group by integration type
            types = {}
            for name, info in data.get("software", {}).items():
                integration_type = info.get("integration_type", "unknown")
                if integration_type not in types:
                    types[integration_type] = {"total": 0, "available": 0}
                types[integration_type]["total"] += 1
                if info.get("available"):
                    types[integration_type]["available"] += 1

            print("\\n  Integration Types:")
            for type_name, stats in types.items():
                rate = (stats["available"] / stats["total"] * 100) if stats["total"] > 0 else 0
                print(f"    - {type_name}: {stats['available']}/{stats['total']} ({rate:.1f}%)")

            return True
        else:
            print(f"  ❌ Software API failed: {response.status_code}")
            return False

    except Exception as e:
        print(f"  ❌ Error checking software: {e}")
        return False


def check_channel_integrations():
    """Check channel integrations"""
    try:
        print("\\n🔍 Checking Channel Integrations...")
        protocol = get_protocol()
        channels = protocol.get_all_channels()

        print(f"  Total Channels: {len(channels)}")

        # Group by channel type
        types = {}
        for channel_id, config in channels.items():
            channel_type = config.channel_type.value
            if channel_type not in types:
                types[channel_type] = 0
            types[channel_type] += 1

        print("  Channel Types:")
        for type_name, count in types.items():
            print(f"    - {type_name}: {count} channels")

        return len(channels) > 0

    except Exception as e:
        print(f"  ❌ Error checking channels: {e}")
        return False


def check_folder_structure():
    """Check key folder integrations"""
    print("\\n🔍 Checking Folder Structure...")

    key_folders = [
        "backend",
        "app",
        "frontend",
        "assets",
        "content",
        "output",
        "agents",
        "marketing_agent",
        "content_agent",
        "orchestrator",
        "tools",
        "scripts",
        "config",
        "data",
# BRACKET_SURGEON: disabled
#     ]

    existing_folders = []
    missing_folders = []

    for folder in key_folders:
        folder_path = Path(folder)
        if folder_path.exists() and folder_path.is_dir():
            existing_folders.append(folder)
        else:
            missing_folders.append(folder)

    print(f"  Existing Folders: {len(existing_folders)}/{len(key_folders)}")
    print(f"  Integration Rate: {(len(existing_folders)/len(key_folders)*100):.1f}%")

    if missing_folders:
        print(f"  Missing: {', '.join(missing_folders)}")

    return len(missing_folders) == 0


def check_api_endpoints():
    """Check key API endpoints"""
    print("\\n🔍 Checking API Endpoints...")

    endpoints = [
        "/health",
        "/dashboard",
        "/dashboard/api/system - info",
        "/system - software/status",
        "/integrations/status",
# BRACKET_SURGEON: disabled
#     ]

    working_endpoints = []
    failed_endpoints = []

    for endpoint in endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            if response.status_code == 200:
                working_endpoints.append(endpoint)
            else:
                failed_endpoints.append(f"{endpoint} ({response.status_code})")
        except Exception:
            failed_endpoints.append(f"{endpoint} (error)")

    print(f"  Working Endpoints: {len(working_endpoints)}/{len(endpoints)}")
    print(f"  Success Rate: {(len(working_endpoints)/len(endpoints)*100):.1f}%")

    if failed_endpoints:
        print(f"  Failed: {', '.join(failed_endpoints)}")

    return len(failed_endpoints) == 0


def main():
    print("🚀 Comprehensive Integration Status Check\\n")

    # Run all checks
    software_ok = check_software_integrations()
    channels_ok = check_channel_integrations()
    folders_ok = check_folder_structure()
    api_ok = check_api_endpoints()

    # Summary
    print("\\n📊 Integration Summary:")
    print(f"  ✅ Software Integrations: {'✓' if software_ok else '✗'}")
    print(f"  ✅ Channel Integrations: {'✓' if channels_ok else '✗'}")
    print(f"  ✅ Folder Structure: {'✓' if folders_ok else '✗'}")
    print(f"  ✅ API Endpoints: {'✓' if api_ok else '✗'}")

    all_integrated = software_ok and channels_ok and folders_ok and api_ok

    if all_integrated:
        print("\\n🎉 ALL FOLDERS AND COMPONENTS ARE FULLY INTEGRATED!")
        print("   System is ready for production operations.")
    else:
        print("\\n⚠️  Some integrations need attention.")
        print("   Review the details above for specific issues.")

    return all_integrated


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)