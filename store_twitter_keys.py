#!/usr/bin/env python3
"""
Script to store Twitter API credentials in the SecretStore
"""

from backend.secret_store import SecretStore


def store_twitter_credentials():
    """Store Twitter API credentials securely"""
    try:
        s = SecretStore()

        # Store Twitter API credentials
        s.store_secret("TWITTER_API_KEY", "1959986824794820608reynolds192")
        s.store_secret("TWITTER_API_SECRET", "your - real - api - secret")
        s.store_secret("TWITTER_ACCESS_TOKEN", "your - real - access - token")
        s.store_secret("TWITTER_ACCESS_TOKEN_SECRET", "your - real - access - token - secret")
        s.store_secret("TWITTER_BEARER_TOKEN", "your - real - bearer - token")

        print("✅ Twitter keys stored successfully")
        print(
            "Note: Replace 'your-real-api-key-here' "
            "and 'your-real-api-secret' with actual credentials"
        )

    except Exception as e:
        print(f"❌ Error storing Twitter keys: {e}")
        return False

    return True


if __name__ == "__main__":
    store_twitter_credentials()