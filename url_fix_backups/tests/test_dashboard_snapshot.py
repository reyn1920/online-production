#!/usr / bin / env python3
"""
Dashboard Snapshot Contract Test
Verifies the /api / dashboard endpoint returns expected structure.
"""

import json
import sys
from typing import Any, Dict

import requests


def test_dashboard_snapshot(base_url: str = "http://127.0.0.1:8083") -> bool:
    """
    Test the dashboard snapshot endpoint for expected structure.

    Args:
        base_url: Base URL of the dashboard service

    Returns:
        bool: True if test passes, False otherwise
    """
    try:
        response = requests.get(f"{base_url}/api / dashboard", timeout=10)

        if response.status_code != 200:
            print(f"❌ Dashboard endpoint returned {response.status_code}")
            return False

        data = response.json()

        # Verify required top - level keys
        required_keys = ["version", "stats", "agents", "timestamp"]
        for key in required_keys:
            if key not in data:
                print(f"❌ Missing required key: {key}")
                return False

        # Verify stats structure
        if "stats" in data and isinstance(data["stats"], dict):
            stats_keys = ["db_size", "backup_count", "uptime_seconds"]
            for key in stats_keys:
                if key not in data["stats"]:
                    print(f"⚠️  Missing stats key: {key}")

        # Verify agents is a list
        if not isinstance(data.get("agents"), list):
            print(f"❌ 'agents' should be a list, got {type(data.get('agents'))}")
            return False

        # Verify timestamp is present and reasonable
        timestamp = data.get("timestamp")
        if not timestamp or not isinstance(timestamp, (int, float)):
            print(f"❌ Invalid timestamp: {timestamp}")
            return False

        print(f"✅ Dashboard snapshot contract test passed")
        print(f"   Version: {data.get('version', 'unknown')}")
        print(f"   Agents: {len(data.get('agents', []))}")
        print(f"   Stats keys: {list(data.get('stats', {}).keys())}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON response: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_metrics_endpoint(base_url: str = "http://127.0.0.1:8083") -> bool:
    """
    Test the metrics endpoint for expected structure.

    Args:
        base_url: Base URL of the dashboard service

    Returns:
        bool: True if test passes, False otherwise
    """
    try:
        response = requests.get(f"{base_url}/api / metrics", timeout=10)

        if response.status_code != 200:
            print(f"❌ Metrics endpoint returned {response.status_code}")
            return False

        data = response.json()

        # Verify required sections
        required_sections = ["system", "database", "version", "timestamp"]
        for section in required_sections:
            if section not in data:
                print(f"❌ Missing required section: {section}")
                return False

        print(f"✅ Metrics endpoint contract test passed")
        return True

    except Exception as e:
        print(f"❌ Metrics test failed: {e}")
        return False


if __name__ == "__main__":
    import sys

    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8083"

    print(f"Testing dashboard contracts at {base_url}")

    dashboard_ok = test_dashboard_snapshot(base_url)
    metrics_ok = test_metrics_endpoint(base_url)

    if dashboard_ok and metrics_ok:
        print("\\n✅ All contract tests passed")
        sys.exit(0)
    else:
        print("\\n❌ Some contract tests failed")
        sys.exit(1)
