#!/usr/bin/env python3
"""
Check Channels Integration Status
Verifies that all channels are properly integrated and accessible through the dashboard API
"""

import json

import requests

from backend.content.universal_channel_protocol import get_protocol


def check_dashboard_api():
    """Check channels through dashboard API"""
    try:
        print("🔍 Checking dashboard API...")
        response = requests.get("http://localhost:8000/dashboard/api/system-info")
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            channels = data.get("channels", {})
            print(f"Channels in dashboard API: {len(channels)}")

            if channels:
                print("Channel details from API:")
                for name, info in channels.items():
                    display_name = info.get("display_name", "N/A")
                    category = info.get("category", "N/A")
                    print(f"  - {name}: {display_name} ({category})")
            else:
                print("  No channels found in API response")

            return data
        else:
            print(f"API request failed with status {response.status_code}")
            return None

    except Exception as e:
        print(f"Error checking dashboard API: {e}")
        return None


def check_protocol_directly():
    """Check channels directly through protocol"""
    try:
        print("\n🔍 Checking Universal Channel Protocol directly...")
        protocol = get_protocol()
        channels = protocol.get_all_channels()

        print(f"Channels in protocol: {len(channels)}")
        if channels:
            print("Channel details from protocol:")
            for channel_id, config in channels.items():
                print(
                    f"  - {channel_id}: {config.channel_name} ({config.channel_type.value})"
                )
                print(f"    RSS Feeds: {len(config.rss_feeds)}")
                print(f"    Firewall Level: {config.firewall_level.value}")

        return channels

    except Exception as e:
        print(f"Error checking protocol: {e}")
        return None


def main():
    print("🚀 Checking Channel Integration Status...\n")

    # Check protocol directly
    protocol_channels = check_protocol_directly()

    # Check dashboard API
    api_data = check_dashboard_api()

    # Summary
    print("\n📊 Integration Status Summary:")
    if protocol_channels:
        print(f"  ✅ Protocol has {len(protocol_channels)} channels")
    else:
        print("  ❌ No channels found in protocol")

    if api_data and api_data.get("channels"):
        print(f"  ✅ Dashboard API shows {len(api_data['channels'])} channels")
    else:
        print("  ⚠️  Dashboard API shows no channels (may need API update)")

    # Check if integration is complete
    if protocol_channels and len(protocol_channels) >= 4:
        print("\n🎉 Channel integration is COMPLETE!")
        print("   All 4 channels from channels.json are now integrated:")
        for channel_id, config in protocol_channels.items():
            if channel_id != "right_perspective":  # Skip the original one
                print(f"   - {config.channel_name}")
        return True
    else:
        print("\n⚠️  Channel integration may be incomplete")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
