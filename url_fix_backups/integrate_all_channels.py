#!/usr / bin / env python3
""""""
Integrate All Channels Script
Integrates all channels from channels.json into the Universal Channel Protocol
""""""

import json
import sys
from pathlib import Path

from backend.content.universal_channel_protocol import (
    ChannelType,
    ContentFirewallLevel,
    get_protocol,
# BRACKET_SURGEON: disabled
# )


def load_channels_config():
    """Load channels configuration from channels.json"""
    try:
        with open("channels.json", "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading channels.json: {e}")
        return None


def map_category_to_channel_type(category):
    """Map channel category to ChannelType enum"""
    mapping = {
        "politics": ChannelType.POLITICAL,
        "technology": ChannelType.TECH,
        "health_wellness": ChannelType.WELLNESS,
        "ai_education": ChannelType.EDUCATION,
# BRACKET_SURGEON: disabled
#     }
    return mapping.get(category, ChannelType.ENTERTAINMENT)


def create_persona_config(channel_data):
    """Create persona configuration from channel data"""
    return {
        "persona_name": channel_data.get("display_name", "Default Persona"),
        "writing_style": channel_data.get(
            "content_style",
            "Professional \"
#     and engaging",
# BRACKET_SURGEON: disabled
#         ),
        "tone_attributes": ["informative", "engaging"],
        "vocabulary_level": "intermediate",
        "humor_style": "light",
        "expertise_areas": [channel_data.get("category", "general")],
        "target_audience": channel_data.get("target_audience", "General audience"),
        "voice_characteristics": {
            "voice": channel_data.get("voice", "Default"),
            "tone": "professional",
# BRACKET_SURGEON: disabled
#         },
        "content_preferences": {
            "length": channel_data.get("target_length", "10 - 15 minutes"),
            "schedule": channel_data.get("posting_schedule", "daily"),
# BRACKET_SURGEON: disabled
#         },
# BRACKET_SURGEON: disabled
#     }


def get_rss_feeds_for_category(category):
    """Get relevant RSS feeds for channel category"""
    feeds = {
        "politics": [
            "https://feeds.foxnews.com / foxnews / politics",
            "https://www.breitbart.com / feed/",
            "https://dailycaller.com / feed/",
# BRACKET_SURGEON: disabled
#         ],
        "technology": [
            "https://techcrunch.com / feed/",
            "https://www.theverge.com / rss / index.xml",
            "https://arstechnica.com / feed/",
# BRACKET_SURGEON: disabled
#         ],
        "health_wellness": [
            "https://www.healthline.com / rss",
            "https://www.medicalnewstoday.com / rss",
            "https://www.webmd.com / rss / rss.aspx?RSSSource = RSS_PUBLIC",
# BRACKET_SURGEON: disabled
#         ],
        "ai_education": [
            "https://ai.googleblog.com / feeds / posts / default",
            "https://openai.com / blog / rss/",
            "https://www.technologyreview.com / feed/",
# BRACKET_SURGEON: disabled
#         ],
# BRACKET_SURGEON: disabled
#     }
    return feeds.get(category, [])


def integrate_all_channels():
    """Integrate all channels from channels.json into the protocol"""
    print("🚀 Integrating all channels into Universal Channel Protocol...")

    # Load channels configuration
    config = load_channels_config()
    if not config:
        print("❌ Failed to load channels configuration")
        return False

    # Get protocol instance
    protocol = get_protocol()

    # Track integration results
    integrated_channels = []
    failed_channels = []

    # Process each channel
    for channel_name, channel_data in config["channels"].items():
        try:
            print(f"\\n📺 Integrating channel: {channel_name}")

            # Generate channel ID from name
            channel_id = channel_name.lower().replace(" ", "_")

            # Skip if already exists
            if protocol.get_channel_config(channel_id):
                print(f"  ✅ Channel already integrated: {channel_id}")
                integrated_channels.append(channel_name)
                continue

            # Map category to channel type
            channel_type = map_category_to_channel_type(channel_data.get("category", "general"))

            # Create persona configuration
            persona_config = create_persona_config(channel_data)

            # Get RSS feeds for category
            rss_feeds = get_rss_feeds_for_category(channel_data.get("category", "general"))

            # Set firewall level (strict for political content)
            firewall_level = (
                ContentFirewallLevel.STRICT
                if channel_data.get("category") == "politics"
                else ContentFirewallLevel.STANDARD
# BRACKET_SURGEON: disabled
#             )

            # Create channel in protocol
            channel_config = protocol.create_channel(
                channel_id=channel_id,
                channel_name=channel_name,
                channel_type=channel_type,
                persona_config=persona_config,
                rss_feeds=rss_feeds,
                firewall_level=firewall_level,
# BRACKET_SURGEON: disabled
#             )

            print(f"  ✅ Successfully integrated: {channel_name}")
            print(f"     - Channel ID: {channel_id}")
            print(f"     - Type: {channel_type.value}")
            print(f"     - Firewall: {firewall_level.value}")
            print(f"     - RSS Feeds: {len(rss_feeds)} feeds")

            integrated_channels.append(channel_name)

        except Exception as e:
            print(f"  ❌ Failed to integrate {channel_name}: {e}")
            failed_channels.append(channel_name)

    # Print summary
    print(f"\\n📊 Integration Summary:")
    print(f"  ✅ Successfully integrated: {len(integrated_channels)} channels")
    for channel in integrated_channels:
        print(f"     - {channel}")

    if failed_channels:
        print(f"  ❌ Failed to integrate: {len(failed_channels)} channels")
        for channel in failed_channels:
            print(f"     - {channel}")

    # Verify final state
    all_channels = protocol.get_all_channels()
    print(f"\\n🎯 Total channels in protocol: {len(all_channels)}")
    for channel_id, config in all_channels.items():
        print(f"  - {config.channel_name} ({config.channel_type.value})")

    return len(failed_channels) == 0


if __name__ == "__main__":
    success = integrate_all_channels()
    if success:
        print("\\n🎉 All channels successfully integrated!")
        sys.exit(0)
    else:
        print("\\n⚠️  Some channels failed to integrate. Check the logs above.")
        sys.exit(1)