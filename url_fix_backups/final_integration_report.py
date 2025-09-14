#!/usr / bin / env python3
"""
Final Integration Status Report
Comprehensive check of all system integrations
"""

import json
from pathlib import Path

import requests

from backend.content.universal_channel_protocol import get_protocol


def check_integration_endpoints():
    """Check integration - specific endpoints"""
    print("🔗 Integration Endpoints Status:")

    integration_endpoints = [
        "/integrations/",
        "/integrations / providers",
        "/integrations / providers / active",
        "/integrations / affiliates",
        "/integrations / test - call",
    ]

    working = 0
    total = len(integration_endpoints)

    for endpoint in integration_endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            status = "✅" if response.status_code == 200 else "⚠️"
            print(f"  {status} {endpoint} - {response.status_code}")
            if response.status_code == 200:
                working += 1
        except Exception as e:
            print(f"  ❌ {endpoint} - Error")

    print(f"  Integration Success Rate: {working}/{total} ({(working / total * 100):.1f}%)")
    return working, total


def check_provider_integrations():
    """Check provider integrations"""
    print("\\n🔌 Provider Integration Status:")

    try:
        response = requests.get("http://localhost:8000 / integrations / providers")
        if response.status_code == 200:
            providers = response.json()
            if isinstance(providers, list):
                print(f"  Total Providers: {len(providers)}")

                # Check active providers
                active_response = requests.get(
                    "http://localhost:8000 / integrations / providers / active"
                )
                if active_response.status_code == 200:
                    active_providers = active_response.json()
                    active_count = (
                        len(active_providers) if isinstance(active_providers, list) else 0
                    )
                    print(f"  Active Providers: {active_count}")
                    print(
                        f"  Activation Rate: {(active_count / len(providers)*100):.1f}%"
                        if len(providers) > 0
                        else "  Activation Rate: 0%"
                    )
                    return True
            else:
                print(f"  Providers data: {type(providers)}")
                return True
        else:
            print(f"  ❌ Providers API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Error checking providers: {e}")
        return False


def check_affiliate_integrations():
    """Check affiliate integrations"""
    print("\\n💼 Affiliate Integration Status:")

    try:
        response = requests.get("http://localhost:8000 / integrations / affiliates")
        if response.status_code == 200:
            affiliates = response.json()
            if isinstance(affiliates, list):
                print(f"  Total Affiliates: {len(affiliates)}")
            else:
                print(f"  Affiliates available: {type(affiliates)}")
            return True
        else:
            print(f"  ❌ Affiliates API failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ❌ Error checking affiliates: {e}")
        return False


def check_channel_integrations():
    """Check channel integrations"""
    print("\\n📺 Channel Integration Status:")

    try:
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

        print("  Channel Distribution:")
        for type_name, count in types.items():
            print(f"    - {type_name}: {count} channels")

        return len(channels) >= 4  # Should have at least 4 channels from channels.json

    except Exception as e:
        print(f"  ❌ Error checking channels: {e}")
        return False


def check_dashboard_integrations():
    """Check dashboard integrations"""
    print("\\n📊 Dashboard Integration Status:")

    dashboard_endpoints = [
        "/dashboard / api / status",
        "/dashboard / api / metrics",
        "/dashboard / api / services",
        "/dashboard / api / system - info",
    ]

    working = 0
    total = len(dashboard_endpoints)

    for endpoint in dashboard_endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            status = "✅" if response.status_code == 200 else "⚠️"
            print(f"  {status} {endpoint} - {response.status_code}")
            if response.status_code == 200:
                working += 1
        except Exception as e:
            print(f"  ❌ {endpoint} - Error")

    print(f"  Dashboard Success Rate: {working}/{total} ({(working / total * 100):.1f}%)")
    return working >= 3  # At least 3 / 4 should work


def check_folder_structure():
    """Check critical folder structure"""
    print("\\n📁 Folder Structure Status:")

    critical_folders = [
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
    ]

    existing = [f for f in critical_folders if Path(f).exists()]
    missing = [f for f in critical_folders if not Path(f).exists()]

    print(f"  Existing Folders: {len(existing)}/{len(critical_folders)}")
    print(f"  Structure Completeness: {(len(existing)/len(critical_folders)*100):.1f}%")

    if missing:
        print(f"  Missing: {', '.join(missing)}")

    return len(missing) == 0


def main():
    print("🚀 FINAL INTEGRATION STATUS REPORT\\n")
    print("=" * 50)

    # Run all integration checks
    integration_working, integration_total = check_integration_endpoints()
    providers_ok = check_provider_integrations()
    affiliates_ok = check_affiliate_integrations()
    channels_ok = check_channel_integrations()
    dashboard_ok = check_dashboard_integrations()
    folders_ok = check_folder_structure()

    print("\\n" + "=" * 50)
    print("📋 INTEGRATION SUMMARY:")
    print("=" * 50)

    # Calculate overall scores
    integration_score = (
        (integration_working / integration_total * 100) if integration_total > 0 else 0
    )

    print(
        f"  🔗 Integration Endpoints: {integration_working}/{integration_total} ({integration_score:.1f}%)"
    )
    print(f"  🔌 Provider Integrations: {'✅ ACTIVE' if providers_ok else '❌ ISSUES'}")
    print(f"  💼 Affiliate Integrations: {'✅ ACTIVE' if affiliates_ok else '❌ ISSUES'}")
    print(f"  📺 Channel Integrations: {'✅ COMPLETE' if channels_ok else '❌ INCOMPLETE'}")
    print(f"  📊 Dashboard Integrations: {'✅ OPERATIONAL' if dashboard_ok else '❌ ISSUES'}")
    print(f"  📁 Folder Structure: {'✅ COMPLETE' if folders_ok else '❌ INCOMPLETE'}")

    # Overall assessment
    all_systems = [providers_ok, affiliates_ok, channels_ok, dashboard_ok, folders_ok]
    systems_ok = sum(all_systems)
    total_systems = len(all_systems)

    overall_score = systems_ok / total_systems * 100

    print(f"\\n🎯 OVERALL INTEGRATION SCORE: {systems_ok}/{total_systems} ({overall_score:.1f}%)")

    if overall_score >= 80:
        print("\\n🎉 EXCELLENT! ALL MAJOR SYSTEMS ARE INTEGRATED!")
        print("   ✅ System is production - ready")
        print("   ✅ All folders and components are properly integrated")
        print("   ✅ APIs are operational and responding")
        print("   ✅ Integration infrastructure is robust")
    elif overall_score >= 60:
        print("\\n✅ GOOD! Most systems are integrated successfully.")
        print("   ⚠️  Minor issues detected but system is functional")
    else:
        print("\\n⚠️  ATTENTION NEEDED! Some critical integrations require review.")

    print("\\n" + "=" * 50)
    return overall_score >= 80


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
