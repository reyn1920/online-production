#!/usr/bin/env python3
"""
Manifest Contract Test
Verifies API endpoints conform to expected schemas and contracts.
"""

import sys

import requests


def validate_version_endpoint(base_url: str) -> bool:
    """
    Validate/api/version endpoint contract.

    Expected schema:
    {
        "service": str,
            "version": str,
            "commit": str,
            "build_time": str,
            "python_version": str
    }
    """
    try:
        response = requests.get(f"{base_url}/api/version", timeout=5)

        if response.status_code != 200:
            print(f"❌ Version endpoint returned {response.status_code}")
            return False

        data = response.json()

        required_fields = [
            "service",
            "version",
            "commit",
            "build_time",
            "python_version",
        ]
        for field in required_fields:
            if field not in data:
                print(f"❌ Version endpoint missing field: {field}")
                return False
            if not isinstance(data[field], str):
                print(f"❌ Version field '{field}' should be string, got {type(data[field])}")
                return False

        print("✅ Version endpoint contract valid")
        return True

    except Exception as e:
        print(f"❌ Version endpoint test failed: {e}")
        return False


def validate_metrics_schema(base_url: str) -> bool:
    """
    Validate/api/metrics endpoint schema.

    Expected top - level structure:
    {
        "system": {...},
            "database": {...},
            "backup": {...},
            "version": {...},
            "agents": [...],
            "errors": {...},
            "timestamp": float
    }
    """
    try:
        response = requests.get(f"{base_url}/api/metrics", timeout=10)

        if response.status_code != 200:
            print(f"❌ Metrics endpoint returned {response.status_code}")
            return False

        data = response.json()

        # Validate top - level structure
        required_sections = ["system", "database", "version", "timestamp"]
        for section in required_sections:
            if section not in data:
                print(f"❌ Metrics missing section: {section}")
                return False

        # Validate system section
        if "system" in data:
            system = data["system"]
            if not isinstance(system, dict):
                print(f"❌ System section should be dict, got {type(system)}")
                return False

        # Validate database section
        if "database" in data:
            database = data["database"]
            if not isinstance(database, dict):
                print(f"❌ Database section should be dict, got {type(database)}")
                return False

        # Validate agents section (if present)
        if "agents" in data:
            agents = data["agents"]
            if not isinstance(agents, list):
                print(f"❌ Agents section should be list, got {type(agents)}")
                return False

        # Validate timestamp
        timestamp = data.get("timestamp")
        if not isinstance(timestamp, (int, float)):
            print(f"❌ Timestamp should be number, got {type(timestamp)}")
            return False

        print("✅ Metrics endpoint schema valid")
        return True

    except Exception as e:
        print(f"❌ Metrics schema test failed: {e}")
        return False


def validate_dashboard_schema(base_url: str) -> bool:
    """
    Validate/api/dashboard endpoint schema.
    """
    try:
        response = requests.get(f"{base_url}/api/dashboard", timeout=10)

        if response.status_code != 200:
            print(f"❌ Dashboard endpoint returned {response.status_code}")
            return False

        data = response.json()

        # Basic structure validation
        if not isinstance(data, dict):
            print(f"❌ Dashboard response should be dict, got {type(data)}")
            return False

        # Check for timestamp
        if "timestamp" in data:
            timestamp = data["timestamp"]
            if not isinstance(timestamp, (int, float)):
                print(f"❌ Dashboard timestamp should be number, got {type(timestamp)}")
                return False

        print("✅ Dashboard endpoint schema valid")
        return True

    except Exception as e:
        print(f"❌ Dashboard schema test failed: {e}")
        return False


def validate_readiness_endpoint(base_url: str) -> bool:
    """
    Validate readiness/health endpoint.
    """
    try:
        # Try common health check endpoints
        endpoints = ["/health", "/ready", "/api/health", "/api/ready"]

        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"✅ Readiness endpoint {endpoint} available")
                    return True
            except Exception:
                continue

        # If no dedicated health endpoint, check if main service responds
        response = requests.get(f"{base_url}/api/version", timeout=5)
        if response.status_code == 200:
            print("✅ Service readiness confirmed via version endpoint")
            return True

        print("❌ No readiness endpoint found")
        return False

    except Exception as e:
        print(f"❌ Readiness test failed: {e}")
        return False


def run_manifest_tests(base_url: str = "http://127.0.0.1:8083") -> bool:
    """
    Run all manifest contract tests.

    Args:
        base_url: Base URL of the service

    Returns:
        bool: True if all tests pass
    """
    print(f"Running manifest contract tests against {base_url}")
    print("=" * 50)

    tests = [
        ("Version Endpoint", lambda: validate_version_endpoint(base_url)),
        ("Metrics Schema", lambda: validate_metrics_schema(base_url)),
        ("Dashboard Schema", lambda: validate_dashboard_schema(base_url)),
        ("Readiness Check", lambda: validate_readiness_endpoint(base_url)),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\\n🧪 Testing {test_name}...")
        try:
            result = test_func()
            results.append(result)
            if result:
                print(f"   ✅ {test_name} passed")
            else:
                print(f"   ❌ {test_name} failed")
        except Exception as e:
            print(f"   ❌ {test_name} error: {e}")
            results.append(False)

    passed = sum(results)
    total = len(results)

    print(f"\\n{'='*50}")
    print(f"Manifest Contract Tests: {passed}/{total} passed")

    if passed == total:
        print("🎉 All manifest contract tests passed!")
        return True
    else:
        print(f"💥 {total - passed} manifest contract tests failed")
        return False


if __name__ == "__main__":
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8083"

    success = run_manifest_tests(base_url)
    sys.exit(0 if success else 1)
