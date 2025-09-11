#!/usr/bin/env python3
"""
Production Secrets Setup Script

This script helps configure all production API keys and secrets needed
to replace fake/mock data with real API integrations.

Usage:
    python scripts/setup_production_secrets.py

Author: TRAE.AI System
Version: 1.0.0
"""

import getpass
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from secret_store import SecretStore


def setup_twitter_credentials(store: SecretStore):
    """Setup Twitter API credentials."""
    print("\n=== Twitter API Configuration ===")
    print("You need to obtain these from https://developer.twitter.com/")
    print("Required credentials:")
    print("1. API Key (Consumer Key)")
    print("2. API Secret (Consumer Secret)")
    print("3. Access Token")
    print("4. Access Token Secret")
    print()

    # Check if credentials already exist
    existing_creds = [
        store.secret_exists("TWITTER_API_KEY"),
        store.secret_exists("TWITTER_API_SECRET"),
        store.secret_exists("TWITTER_ACCESS_TOKEN"),
        store.secret_exists("TWITTER_ACCESS_TOKEN_SECRET"),
    ]

    if all(existing_creds):
        print("✓ Twitter credentials already configured")
        update = input("Update existing credentials? (y/N): ").lower().startswith("y")
        if not update:
            return

    # Get credentials from user
    api_key = getpass.getpass("Enter Twitter API Key: ").strip()
    api_secret = getpass.getpass("Enter Twitter API Secret: ").strip()
    access_token = getpass.getpass("Enter Twitter Access Token: ").strip()
    access_token_secret = getpass.getpass("Enter Twitter Access Token Secret: ").strip()

    if not all([api_key, api_secret, access_token, access_token_secret]):
        print("❌ All Twitter credentials are required")
        return False

    # Store credentials
    try:
        store.store_secret("TWITTER_API_KEY", api_key)
        store.store_secret("TWITTER_API_SECRET", api_secret)
        store.store_secret("TWITTER_ACCESS_TOKEN", access_token)
        store.store_secret("TWITTER_ACCESS_TOKEN_SECRET", access_token_secret)
        print("✓ Twitter credentials stored successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to store Twitter credentials: {e}")
        return False


def setup_youtube_credentials(store: SecretStore):
    """Setup YouTube Data API and OAuth credentials."""
    print("\n=== YouTube API Configuration ===")
    print("You need to obtain these from https://console.cloud.google.com/")
    print("Required credentials:")
    print("1. YouTube Data API v3 Key")
    print("2. OAuth 2.0 Client ID")
    print("3. OAuth 2.0 Client Secret")
    print("4. Channel ID (optional)")
    print()

    # Check if credentials already exist
    existing_creds = [
        store.secret_exists("YOUTUBE_API_KEY"),
        store.secret_exists("YOUTUBE_CLIENT_ID"),
        store.secret_exists("YOUTUBE_CLIENT_SECRET"),
    ]

    if all(existing_creds):
        print("✓ YouTube credentials already configured")
        update = input("Update existing credentials? (y/N): ").lower().startswith("y")
        if not update:
            return

    # Get credentials from user
    api_key = getpass.getpass("Enter YouTube Data API Key: ").strip()
    client_id = input("Enter OAuth 2.0 Client ID: ").strip()
    client_secret = getpass.getpass("Enter OAuth 2.0 Client Secret: ").strip()
    channel_id = input("Enter YouTube Channel ID (optional): ").strip()

    if not all([api_key, client_id, client_secret]):
        print("❌ API Key, Client ID, and Client Secret are required")
        return False

    try:
        store.store_secret("YOUTUBE_API_KEY", api_key)
        store.store_secret("YOUTUBE_CLIENT_ID", client_id)
        store.store_secret("YOUTUBE_CLIENT_SECRET", client_secret)
        if channel_id:
            store.store_secret("YOUTUBE_CHANNEL_ID", channel_id)
        print("✓ YouTube credentials stored successfully")
        print(
            "\n⚠️  Note: You'll need to complete OAuth flow to get access/refresh tokens"
        )
        print("   Run the YouTube integration setup after this to authorize the app")
        return True
    except Exception as e:
        print(f"❌ Failed to store YouTube credentials: {e}")
        return False


def setup_instagram_credentials(store: SecretStore):
    """Setup Instagram Basic Display API credentials."""
    print("\n=== Instagram API Configuration ===")
    print("You need to obtain these from https://developers.facebook.com/")
    print("Required credentials:")
    print("1. Instagram App ID")
    print("2. Instagram App Secret")
    print("3. Instagram Access Token")
    print()

    existing_creds = [
        store.secret_exists("INSTAGRAM_APP_ID"),
        store.secret_exists("INSTAGRAM_APP_SECRET"),
        store.secret_exists("INSTAGRAM_ACCESS_TOKEN"),
    ]

    if all(existing_creds):
        print("✓ Instagram credentials already configured")
        update = input("Update existing credentials? (y/N): ").lower().startswith("y")
        if not update:
            return

    app_id = input("Enter Instagram App ID: ").strip()
    app_secret = getpass.getpass("Enter Instagram App Secret: ").strip()
    access_token = getpass.getpass("Enter Instagram Access Token: ").strip()

    if not all([app_id, app_secret, access_token]):
        print("❌ All Instagram credentials are required")
        return False

    try:
        store.store_secret("INSTAGRAM_APP_ID", app_id)
        store.store_secret("INSTAGRAM_APP_SECRET", app_secret)
        store.store_secret("INSTAGRAM_ACCESS_TOKEN", access_token)
        print("✓ Instagram credentials stored successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to store Instagram credentials: {e}")
        return False


def setup_tiktok_credentials(store: SecretStore):
    """Setup TikTok API credentials."""
    print("\n=== TikTok API Configuration ===")
    print("You need to obtain these from https://developers.tiktok.com/")
    print("Required credentials:")
    print("1. TikTok Client Key")
    print("2. TikTok Client Secret")
    print("3. TikTok Access Token")
    print()

    existing_creds = [
        store.secret_exists("TIKTOK_CLIENT_KEY"),
        store.secret_exists("TIKTOK_CLIENT_SECRET"),
        store.secret_exists("TIKTOK_ACCESS_TOKEN"),
    ]

    if all(existing_creds):
        print("✓ TikTok credentials already configured")
        update = input("Update existing credentials? (y/N): ").lower().startswith("y")
        if not update:
            return

    client_key = input("Enter TikTok Client Key: ").strip()
    client_secret = getpass.getpass("Enter TikTok Client Secret: ").strip()
    access_token = getpass.getpass("Enter TikTok Access Token: ").strip()

    if not all([client_key, client_secret, access_token]):
        print("❌ All TikTok credentials are required")
        return False

    try:
        store.store_secret("TIKTOK_CLIENT_KEY", client_key)
        store.store_secret("TIKTOK_CLIENT_SECRET", client_secret)
        store.store_secret("TIKTOK_ACCESS_TOKEN", access_token)
        print("✓ TikTok credentials stored successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to store TikTok credentials: {e}")
        return False


def setup_google_trends_credentials(store: SecretStore):
    """Setup Google Trends API credentials."""
    print("\n=== Google Trends API Configuration ===")
    print("You need to obtain this from https://console.cloud.google.com/")
    print("Required: Google Trends API Key")
    print()

    if store.secret_exists("GOOGLE_TRENDS_API_KEY"):
        print("✓ Google Trends API key already configured")
        update = input("Update existing key? (y/N): ").lower().startswith("y")
        if not update:
            return

    api_key = getpass.getpass("Enter Google Trends API Key: ").strip()

    if not api_key:
        print("❌ Google Trends API key is required")
        return False

    try:
        store.store_secret("GOOGLE_TRENDS_API_KEY", api_key)
        print("✓ Google Trends API key stored successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to store Google Trends API key: {e}")
        return False


def test_twitter_connection(store: SecretStore):
    """Test Twitter API connection."""
    print("\n=== Testing Twitter Connection ===")

    try:
        sys.path.insert(
            0, str(Path(__file__).parent.parent / "backend" / "integrations")
        )
        from twitter_integration import TwitterIntegration

        twitter = TwitterIntegration()
        if twitter.test_connection():
            print("✓ Twitter API connection successful")
            return True
        else:
            print("❌ Twitter API connection failed")
            return False
    except Exception as e:
        print(f"❌ Twitter connection test failed: {e}")
        return False


def main():
    """Main setup function."""
    print("TRAE.AI Production Secrets Setup")
    print("=" * 40)
    print("This script will help you configure production API credentials")
    print("to replace mock/fake data with real platform integrations.")
    print()

    # Check for master key
    if not os.getenv("TRAE_MASTER_KEY"):
        print("❌ TRAE_MASTER_KEY environment variable not set")
        print("Please set it before running this script:")
        print("export TRAE_MASTER_KEY=your_secure_master_key")
        return 1

    # Initialize secret store
    try:
        db_path = Path(__file__).parent.parent / "data" / "secrets.sqlite"
        db_path.parent.mkdir(exist_ok=True)

        with SecretStore(str(db_path)) as store:
            print(f"✓ Connected to secret store: {db_path}")

            # Setup each service
            services = [
                ("Twitter", setup_twitter_credentials),
                ("YouTube", setup_youtube_credentials),
                ("Instagram", setup_instagram_credentials),
                ("TikTok", setup_tiktok_credentials),
                ("Google Trends", setup_google_trends_credentials),
            ]

            for service_name, setup_func in services:
                try:
                    setup_func(store)
                except KeyboardInterrupt:
                    print(f"\n❌ Setup cancelled for {service_name}")
                    break
                except Exception as e:
                    print(f"❌ Error setting up {service_name}: {e}")

            # Test connections
            print("\n=== Testing Connections ===")
            test_twitter_connection(store)

            print("\n=== Setup Complete ===")
            print("Your production secrets have been configured.")
            print("The system will now use real API data instead of mock data.")

    except Exception as e:
        print(f"❌ Failed to initialize secret store: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
