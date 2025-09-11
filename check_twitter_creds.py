#!/usr/bin/env python3

from backend.secret_store import SecretStore


def check_twitter_credentials():
    """Check Twitter credentials in secret store"""
    try:
        store = SecretStore()
        twitter_creds = [
            "TWITTER_API_KEY",
            "TWITTER_API_SECRET",
            "TWITTER_ACCESS_TOKEN",
            "TWITTER_ACCESS_TOKEN_SECRET",
        ]

        print("\n🐦 Twitter/X Credentials Status:")
        print("=" * 40)

        missing_creds = []
        for cred in twitter_creds:
            value = store.get_secret(cred)
            status = "SET" if value else "MISSING"
            icon = "✅" if value else "❌"
            print(f"  {icon} {cred}: {status}")
            if not value:
                missing_creds.append(cred)

        print("\n📊 Summary:")
        print(f"  Total credentials: {len(twitter_creds)}")
        print(f"  Configured: {len(twitter_creds) - len(missing_creds)}")
        print(f"  Missing: {len(missing_creds)}")

        if missing_creds:
            print("\n⚠️  Missing credentials:")
            for cred in missing_creds:
                print(f"    - {cred}")
            print("\n💡 To fix: Run the setup script to configure Twitter credentials:")
            print("    python scripts/setup_production_secrets.py")
        else:
            print("\n✅ All Twitter credentials are configured!")

    except Exception as e:
        print(f"❌ Error checking credentials: {e}")


if __name__ == "__main__":
    check_twitter_credentials()
