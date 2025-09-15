#!/usr/bin/env python3
""""""
Final Integration Status Report
Comprehensive check of all system integrations
""""""

from pathlib import Path

import requests

from backend.content.universal_channel_protocol import get_protocol


def check_integration_endpoints():
    """Check integration-specific endpoints"""
    print("🔗 Integration Endpoints Status:")

    integration_endpoints = [
        "integrations/",
        "integrations/providers",
        "integrations/providers/active",
        "integrations/affiliates",
        "integrations/test-call",
# BRACKET_SURGEON: disabled
#     ]

    working = 0
    total = len(integration_endpoints)

    for endpoint in integration_endpoints:
        try:
            response = requests.get(f"http://localhost:8002/api/{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {endpoint} - OK")
                working += 1
            else:
                print(f"  ❌ {endpoint} - Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {endpoint} - Error: {e}")

    print(f"\n📊 Integration Endpoints: {working}/{total} working")
    return working == total


def check_content_integrations():
    """Check content system integrations"""
    print("\n📝 Content System Integrations:")

    content_endpoints = [
        "content/channels",
        "content/protocols",
        "content/universal",
        "content/validation",
        "content/processing",
# BRACKET_SURGEON: disabled
#     ]

    working = 0
    total = len(content_endpoints)

    for endpoint in content_endpoints:
        try:
            response = requests.get(f"http://localhost:8002/api/{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {endpoint} - OK")
                working += 1
            else:
                print(f"  ❌ {endpoint} - Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {endpoint} - Error: {e}")

    print(f"\n📊 Content Integrations: {working}/{total} working")
    return working == total


def check_protocol_integrations():
    """Check universal channel protocol integrations"""
    print("\n🔄 Protocol Integrations:")

    try:
        protocol = get_protocol()
        if protocol:
            print("  ✅ Universal Channel Protocol - Loaded")

            # Test protocol methods
            test_methods = [
                "validate_channel",
                "process_content",
                "handle_request",
                "format_response",
# BRACKET_SURGEON: disabled
#             ]

            working_methods = 0
            for method in test_methods:
                if hasattr(protocol, method):
                    print(f"    ✅ {method} - Available")
                    working_methods += 1
                else:
                    print(f"    ❌ {method} - Missing")

            print(f"\n📊 Protocol Methods: {working_methods}/{len(test_methods)} available")
            return working_methods == len(test_methods)
        else:
            print("  ❌ Universal Channel Protocol - Failed to load")
            return False
    except Exception as e:
        print(f"  ❌ Protocol Integration Error: {e}")
        return False


def check_affiliate_integrations():
    """Check affiliate system integrations"""
    print("\n💰 Affiliate System Integrations:")

    affiliate_endpoints = [
        "affiliates/programs",
        "affiliates/tracking",
        "affiliates/commissions",
        "affiliates/payouts",
        "affiliates/reports",
# BRACKET_SURGEON: disabled
#     ]

    working = 0
    total = len(affiliate_endpoints)

    for endpoint in affiliate_endpoints:
        try:
            response = requests.get(f"http://localhost:8002/api/{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {endpoint} - OK")
                working += 1
            else:
                print(f"  ❌ {endpoint} - Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {endpoint} - Error: {e}")

    print(f"\n📊 Affiliate Integrations: {working}/{total} working")
    return working == total


def check_api_integrations():
    """Check external API integrations"""
    print("\n🌐 External API Integrations:")

    api_endpoints = [
        "api/health",
        "api/status",
        "api/version",
        "api/metrics",
        "api/system-stats",
# BRACKET_SURGEON: disabled
#     ]

    working = 0
    total = len(api_endpoints)

    for endpoint in api_endpoints:
        try:
            response = requests.get(f"http://localhost:8002/{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {endpoint} - OK")
                working += 1
            else:
                print(f"  ❌ {endpoint} - Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {endpoint} - Error: {e}")

    print(f"\n📊 API Integrations: {working}/{total} working")
    return working == total


def check_dashboard_integrations():
    """Check dashboard system integrations"""
    print("\n📊 Dashboard System Integrations:")

    dashboard_endpoints = [
        "dashboard/stats",
        "dashboard/metrics",
        "dashboard/health",
        "dashboard/performance",
        "dashboard/alerts",
# BRACKET_SURGEON: disabled
#     ]

    working = 0
    total = len(dashboard_endpoints)

    for endpoint in dashboard_endpoints:
        try:
            response = requests.get(f"http://localhost:8002/api/{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {endpoint} - OK")
                working += 1
            else:
                print(f"  ❌ {endpoint} - Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ {endpoint} - Error: {e}")

    print(f"\n📊 Dashboard Integrations: {working}/{total} working")
    return working == total


def check_file_integrations():
    """Check file system integrations"""
    print("\n📁 File System Integrations:")

    critical_paths = [
        Path("backend/content"),
        Path("backend/integrations"),
        Path("backend/affiliates"),
        Path("backend/dashboard"),
        Path("backend/api"),
# BRACKET_SURGEON: disabled
#     ]

    working = 0
    total = len(critical_paths)

    for path in critical_paths:
        if path.exists():
            print(f"  ✅ {path} - Exists")
            working += 1
        else:
            print(f"  ❌ {path} - Missing")

    print(f"\n📊 File System: {working}/{total} paths available")
    return working == total


def generate_integration_report():
    """Generate comprehensive integration report"""
    print("\n📋 Final Integration Report:")
    print("=" * 50)

    results = {
        "Integration Endpoints": check_integration_endpoints(),
        "Content System": check_content_integrations(),
        "Protocol System": check_protocol_integrations(),
        "Affiliate System": check_affiliate_integrations(),
        "API System": check_api_integrations(),
        "Dashboard System": check_dashboard_integrations(),
        "File System": check_file_integrations(),
# BRACKET_SURGEON: disabled
#     }

    working_systems = sum(1 for status in results.values() if status)
    total_systems = len(results)

    print("\n🎯 Integration Summary:")
    for system, status in results.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {system}")

    print(f"\n📊 Overall Status: {working_systems}/{total_systems} systems operational")
    success_rate = (working_systems / total_systems) * 100
    print(f"🎯 Success Rate: {success_rate:.1f}%")

    if success_rate >= 80:
        print("\n🎉 Integration Status: EXCELLENT")
    elif success_rate >= 60:
        print("\n⚠️  Integration Status: GOOD (Some issues detected)")
    else:
        print("\n❌ Integration Status: CRITICAL (Major issues detected)")

    return working_systems == total_systems


def main():
    """Main integration check function"""
    print("🚀 Final Integration Status Report")
    print("=" * 60)
    print("Checking all system integrations...\n")

    try:
        success = generate_integration_report()

        if success:
            print("\n✅ All integrations are working correctly!")
            print("🎯 System is ready for production deployment.")
        else:
            print("\n⚠️  Some integrations have issues.")
            print("🔧 Please review and fix the reported problems.")

        return success
    except Exception as e:
        print(f"\n❌ Critical error during integration check: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)