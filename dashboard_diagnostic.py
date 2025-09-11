#!/usr / bin / env python3
"""
Dashboard Diagnostic Tool
Comprehensive testing and verification of dashboard functionality
"""

import json
import sys
from datetime import datetime

import requests


def test_dashboard_endpoints():
    """Test all dashboard endpoints and functionality."""
    base_url = "http://localhost:8000"
    results = []

    print("🔍 Dashboard Diagnostic Report")
    print("=" * 50)
    print(f"Testing dashboard at: {base_url}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()

    # Test cases
    test_cases = [
        {
            "name": "Dashboard Home Page",
                "url": f"{base_url}/dashboard/",
                "method": "GET",
                "expected_status": 200,
                "check_content": "Production Dashboard",
                },
            {
            "name": "Dashboard Metrics API",
                "url": f"{base_url}/dashboard / api / metrics",
                "method": "GET",
                "expected_status": 200,
                "check_json": True,
                },
            {
            "name": "Dashboard Services API",
                "url": f"{base_url}/dashboard / api / services",
                "method": "GET",
                "expected_status": 200,
                "check_json": True,
                },
            {
            "name": "Dashboard System Info API",
                "url": f"{base_url}/dashboard / api / system - info",
                "method": "GET",
                "expected_status": 200,
                "check_json": True,
                },
            {
            "name": "Main API Health Check",
                "url": f"{base_url}/health",
                "method": "GET",
                "expected_status": 200,
                "check_json": True,
                },
            {
            "name": "API Documentation",
                "url": f"{base_url}/docs",
                "method": "GET",
                "expected_status": 200,
                "check_content": "FastAPI",
                },
            ]

    passed = 0
    failed = 0

    for test in test_cases:
        try:
            print(f"Testing: {test['name']}")

            if test["method"] == "GET":
                response = requests.get(test["url"], timeout = 10)
            else:
                response = requests.post(test["url"], timeout = 10)

            # Check status code
            if response.status_code == test["expected_status"]:
                status = "✅ PASS"
                passed += 1

                # Additional content checks
                if test.get("check_content"):
                    if test["check_content"] in response.text:
                        print(f"  Status: {status} - Content check passed")
                    else:
                        print(
                            f"  Status: ⚠️  PARTIAL - Status OK but content check failed"
                        )

                elif test.get("check_json"):
                    try:
                        json_data = response.json()
                        print(f"  Status: {status} - JSON response valid")
                        if "status" in json_data:
                            print(f"  Response status: {json_data.get('status')}")
                    except json.JSONDecodeError:
                        print(f"  Status: ⚠️  PARTIAL - Status OK but invalid JSON")
                else:
                    print(f"  Status: {status}")

            else:
                status = "❌ FAIL"
                failed += 1
                print(
                    f"  Status: {status} - Expected {test['expected_status']}, got {response.status_code}"
                )

            results.append(
                {
                    "test": test["name"],
                        "status": (
                        "PASS"
                        if response.status_code == test["expected_status"]
                        else "FAIL"
                    ),
                        "status_code": response.status_code,
                        "response_time": response.elapsed.total_seconds(),
                        }
            )

        except requests.exceptions.ConnectionError:
            print(f"  Status: ❌ FAIL - Connection refused (server not running?)")
            failed += 1
            results.append(
                {"test": test["name"], "status": "FAIL", "error": "Connection refused"}
            )

        except requests.exceptions.Timeout:
            print(f"  Status: ❌ FAIL - Request timeout")
            failed += 1
            results.append({"test": test["name"], "status": "FAIL", "error": "Timeout"})

        except Exception as e:
            print(f"  Status: ❌ FAIL - {str(e)}")
            failed += 1
            results.append({"test": test["name"], "status": "FAIL", "error": str(e)})

        print()

    # Summary
    print("📊 Test Summary")
    print("=" * 30)
    print(f"Total tests: {len(test_cases)}")
    print(f"Passed: {passed} ✅")
    print(f"Failed: {failed} ❌")
    print(f"Success rate: {(passed / len(test_cases)*100):.1f}%")
    print()

    # Dashboard - specific diagnostics
    print("🔧 Dashboard Diagnostics")
    print("=" * 30)

    try:
        # Test dashboard metrics
        metrics_response = requests.get(f"{base_url}/dashboard / api / metrics", timeout = 5)
        if metrics_response.status_code == 200:
            metrics_data = metrics_response.json()
            print("Dashboard Metrics:")
            if "metrics" in metrics_data:
                for key, value in metrics_data["metrics"].items():
                    print(f"  {key}: {value}")
            print()

        # Test dashboard services
        services_response = requests.get(
            f"{base_url}/dashboard / api / services", timeout = 5
        )
        if services_response.status_code == 200:
            services_data = services_response.json()
            print("Service Status:")
            if "services" in services_data:
                for service, info in services_data["services"].items():
                    status = info.get("status", "unknown")
                    last_run = info.get("last_run", "never")
                    print(f"  {service}: {status} (last run: {last_run})")
            print()

    except Exception as e:
        print(f"Error getting dashboard data: {e}")
        print()

    # Recommendations
    print("💡 Recommendations")
    print("=" * 30)

    if failed == 0:
        print("✅ All dashboard tests passed!")
        print("✅ Dashboard is fully operational")
        print("✅ Access dashboard at: http://localhost:8000 / dashboard/")
    else:
        print("⚠️  Some tests failed. Check the following:")
        print("   1. Ensure the server is running on port 8000")
        print("   2. Check server logs for any import errors")
        print("   3. Verify all required dependencies are installed")
        print("   4. Check firewall settings if accessing remotely")

    print()
    print("🌐 Dashboard Access URLs:")
    print(f"   Main Dashboard: {base_url}/dashboard/")
    print(f"   API Metrics: {base_url}/dashboard / api / metrics")
    print(f"   API Services: {base_url}/dashboard / api / services")
    print(f"   System Info: {base_url}/dashboard / api / system - info")
    print(f"   API Docs: {base_url}/docs")

    return passed == len(test_cases)

if __name__ == "__main__":
    success = test_dashboard_endpoints()
    sys.exit(0 if success else 1)
