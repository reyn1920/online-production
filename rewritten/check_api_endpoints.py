#!/usr/bin/env python3
""""""
Check Available API Endpoints
""""""


import requests


def main():
    print("🔍 Checking Available API Endpoints...\\n")

    try:
        # Check OpenAPI spec
        response = requests.get("http://localhost:8000/openapi.json")
        if response.status_code == 200:
            data = response.json()
            paths = list(data.get("paths", {}).keys())

            print(f"Total API Endpoints: {len(paths)}")
            print("\\nAvailable Endpoints:")

            for path in sorted(paths):
                print(f"  - {path}")

            # Check specific integration endpoints
            integration_endpoints = [p for p in paths if "integration" in p.lower()]
            software_endpoints = [p for p in paths if "software" in p.lower()]
            dashboard_endpoints = [p for p in paths if "dashboard" in p.lower()]

            print(f"\\nIntegration - related endpoints: {len(integration_endpoints)}")
            for endpoint in integration_endpoints:
                print(f"  - {endpoint}")

            print(f"\\nSoftware - related endpoints: {len(software_endpoints)}")
            for endpoint in software_endpoints:
                print(f"  - {endpoint}")

            print(f"\\nDashboard - related endpoints: {len(dashboard_endpoints)}")
            for endpoint in dashboard_endpoints:
                print(f"  - {endpoint}")

        else:
            print(f"❌ Failed to get OpenAPI spec: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")

    # Test key endpoints
    print("\\n🧪 Testing Key Endpoints:")
    test_endpoints = [
        "/health",
        "/dashboard",
        "/dashboard/api/system - info",
        "/docs",
        "/openapi.json",
# BRACKET_SURGEON: disabled
#     ]

    for endpoint in test_endpoints:
        try:
            response = requests.get(f"http://localhost:8000{endpoint}", timeout=5)
            status = "✅" if response.status_code == 200 else "⚠️"
            print(f"  {status} {endpoint} - {response.status_code}")
        except Exception as e:
            print(f"  ❌ {endpoint} - Error: {str(e)[:50]}")


if __name__ == "__main__":
    main()