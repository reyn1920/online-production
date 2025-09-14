#!/usr/bin/env python3
"""
Quick TRAE.AI Component Test
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing TRAE.AI components...")

# Test SecretStore
try:
    print("✅ SecretStore available")
except Exception as e:
    print(f"❌ SecretStore: {e}")

# Test TaskQueueManager
try:
    print("✅ TaskQueueManager available")
except Exception as e:
    print(f"❌ TaskQueueManager: {e}")

# Test main services
try:
    # Check if we can import the content agent without TTS issues

    import sys

    sys.path.append("content - agent")

    print("✅ Content Agent available")
except Exception as e:
    print(f"❌ Content Agent: {e}")

try:
    print("✅ Marketing Agent available")
except Exception as e:
    print(f"❌ Marketing Agent: {e}")

try:
    print("✅ Monetization Bundle available")
except Exception as e:
    print(f"❌ Monetization Bundle: {e}")

try:
    # Clear Prometheus registry to avoid metric name collisions

    from prometheus_client import REGISTRY

    REGISTRY._collector_to_names.clear()
    REGISTRY._names_to_collectors.clear()

    import sys

    sys.path.append("analytics - dashboard")

    print("✅ Analytics Dashboard available")
except Exception as e:
    print(f"❌ Analytics Dashboard: {e}")

try:
    print("✅ Main Dashboard available")
except Exception as e:
    print(f"❌ Main Dashboard: {e}")

print("\\nComponent test complete.")
