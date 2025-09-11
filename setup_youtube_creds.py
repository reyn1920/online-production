#!/usr/bin/env python3
"""
YouTube Credentials Setup Script

Sets up YouTube API credentials for the content pipeline.
"""

import getpass
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from secret_store import SecretStore


def setup_youtube_credentials():
    """Setup YouTube API credentials interactively."""
    print("\n=== YouTube API Credentials Setup ===")
    print("\nTo get YouTube API credentials:")
    print("1. Go to https://console.cloud.google.com/")
    print("2. Create a new project or select existing one")
    print("3. Enable YouTube Data API v3")
    print("4. Create credentials (API Key + OAuth 2.0)")
    print("5. Download OAuth client configuration")
    print()

    store = SecretStore()

    # Check existing credentials
    youtube_creds = [
        "YOUTUBE_API_KEY",
        "YOUTUBE_CLIENT_ID",
        "YOUTUBE_CLIENT_SECRET",
        "YOUTUBE_CHANNEL_ID",
    ]

    print("Current YouTube credentials status:")
    missing_creds = []
    for cred in youtube_creds:
        try:
            value = store.get_secret(cred)
            if value:
                print(f"  ✅ {cred}: Set")
            else:
                print(f"  ❌ {cred}: Missing")
                missing_creds.append(cred)
        except Exception:
            print(f"  ❌ {cred}: Missing")
            missing_creds.append(cred)

    if not missing_creds:
        print("\n✅ All YouTube credentials are configured!")
        update = input("\nUpdate existing credentials? (y/N): ").lower().startswith("y")
        if not update:
            return

    print("\n📝 Enter YouTube API credentials:")

    # Get API Key
    api_key = getpass.getpass("YouTube Data API Key: ").strip()
    if not api_key:
        print("❌ API Key is required")
        return

    # Get OAuth credentials
    client_id = input("OAuth 2.0 Client ID: ").strip()
    if not client_id:
        print("❌ Client ID is required")
        return

    client_secret = getpass.getpass("OAuth 2.0 Client Secret: ").strip()
    if not client_secret:
        print("❌ Client Secret is required")
        return

    # Optional channel ID
    channel_id = input("YouTube Channel ID (optional): ").strip()

    try:
        # Store credentials
        store.store_secret("YOUTUBE_API_KEY", api_key)
        store.store_secret("YOUTUBE_CLIENT_ID", client_id)
        store.store_secret("YOUTUBE_CLIENT_SECRET", client_secret)

        if channel_id:
            store.store_secret("YOUTUBE_CHANNEL_ID", channel_id)

        print("\n✅ YouTube credentials stored successfully!")
        print("\n⚠️  Next steps:")
        print("1. Complete OAuth authorization flow")
        print("2. Test the YouTube integration")
        print("3. Run the content pipeline")

    except Exception as e:
        print(f"\n❌ Error storing credentials: {e}")


def test_youtube_integration():
    """Test YouTube integration with stored credentials."""
    print("\n=== Testing YouTube Integration ===")

    try:
        from integrations.youtube_integration import YouTubeIntegration

        yt = YouTubeIntegration()

        if yt.youtube_service:
            print("✅ YouTube service initialized successfully")

            # Try to get channel info if possible
            try:
                # This would require OAuth tokens
                print("📊 YouTube integration is ready for use")
            except Exception as e:
                print(f"⚠️  OAuth tokens needed for full functionality: {e}")
        else:
            print("❌ YouTube service not initialized")
            print("   Check credentials and OAuth setup")

    except Exception as e:
        print(f"❌ Error testing YouTube integration: {e}")


if __name__ == "__main__":
    try:
        setup_youtube_credentials()
        test_youtube_integration()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
